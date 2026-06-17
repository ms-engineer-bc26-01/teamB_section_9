"""outfit_items hybrid persistence

提案コーデ（手持ち＋補完アイテム）を永続化できるよう outfit_items の役割を変更する。
id PK / clothes_id nullable / source_type / item_snapshot。あわせて 2 head をマージ。

Revision ID: a1b2c3d4e5f6
Revises: b7d3a1c9e2f4, 37168f27136b
Create Date: 2026-06-17 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = ("b7d3a1c9e2f4", "37168f27136b")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- outfit_items: 提案アイテム（手持ち/補完）を保存できる構造へ ---
    # 既存行（旧 suggest 保存の owned）は id 採番 + source_type=owned で埋める。
    op.add_column(
        "outfit_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.add_column(
        "outfit_items",
        sa.Column(
            "source_type",
            sa.String(length=20),
            nullable=False,
            server_default="owned",
        ),
    )
    op.create_check_constraint(
        "ck_outfit_items_source_type",
        "outfit_items",
        "source_type IN ('owned', 'suggested')",
    )
    op.add_column(
        "outfit_items",
        sa.Column(
            "item_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "outfit_items",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 複合PK -> id 単独PK、clothes_id を nullable 化
    op.drop_constraint("outfit_items_pkey", "outfit_items", type_="primary")
    op.alter_column(
        "outfit_items",
        "clothes_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.create_primary_key("outfit_items_pkey", "outfit_items", ["id"])

    # 服削除時は履歴を残すため CASCADE -> SET NULL（補完表示は item_snapshot で継続）
    op.drop_constraint(
        "outfit_items_clothes_id_fkey", "outfit_items", type_="foreignkey"
    )
    op.create_foreign_key(
        "outfit_items_clothes_id_fkey",
        "outfit_items",
        "clothes",
        ["clothes_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # backfill 用の server_default は除去（アプリ側で uuid4 / 明示値を入れる）
    op.alter_column("outfit_items", "id", server_default=None)
    op.alter_column("outfit_items", "source_type", server_default=None)

    # --- outfits: 保存フローでは天気要約を持たないため nullable 化 ---
    op.alter_column(
        "outfits",
        "weather_summary",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema.

    注: source_type=suggested（clothes_id=null）の行が存在する場合、複合PK/NOT NULL の
    復元は失敗する。downgrade は補完アイテム未保存の状態を前提とする。
    """
    op.alter_column(
        "outfits",
        "weather_summary",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.drop_constraint(
        "outfit_items_clothes_id_fkey", "outfit_items", type_="foreignkey"
    )
    op.create_foreign_key(
        "outfit_items_clothes_id_fkey",
        "outfit_items",
        "clothes",
        ["clothes_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("outfit_items_pkey", "outfit_items", type_="primary")
    op.alter_column(
        "outfit_items",
        "clothes_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_primary_key(
        "outfit_items_pkey", "outfit_items", ["outfit_id", "clothes_id"]
    )

    op.drop_constraint("ck_outfit_items_source_type", "outfit_items", type_="check")
    op.drop_column("outfit_items", "created_at")
    op.drop_column("outfit_items", "item_snapshot")
    op.drop_column("outfit_items", "source_type")
    op.drop_column("outfit_items", "id")
