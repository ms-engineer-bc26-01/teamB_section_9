"""create users table

Revision ID: 62bcff165381
Revises:
Create Date: 2026-05-26 14:45:19.689868

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '62bcff165381'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("default_region_code", sa.String(length=5), nullable=True),
        sa.Column(
            "subscription_status",
            sa.String(length=20),
            server_default="free",
            nullable=False,
        ),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "clothes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("pattern", sa.String(length=20), nullable=True),
        sa.Column("size", sa.String(length=50), nullable=True),
        sa.Column("season", postgresql.ARRAY(sa.String(length=20)), nullable=False),
        sa.Column("image_url", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=512), nullable=True),
        sa.Column("memo", sa.String(length=200), nullable=True),
        sa.Column(
            "is_favorite",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("wear_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_worn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "outfits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tpo", sa.String(length=20), nullable=False),
        sa.Column("region_code", sa.String(length=5), nullable=False),
        sa.Column("weather_summary", sa.String(length=255), nullable=False),
        sa.Column("weather_temp_max", sa.Float(), nullable=True),
        sa.Column("weather_temp_min", sa.Float(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "is_favorite",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "stripe_subscription_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("stripe_price_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "clothes_tpo",
        sa.Column("clothes_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tpo_tag", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["clothes_id"], ["clothes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("clothes_id", "tpo_tag"),
    )
    op.create_table(
        "outfit_items",
        sa.Column("outfit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clothes_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["clothes_id"], ["clothes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["outfit_id"], ["outfits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("outfit_id", "clothes_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("outfit_items")
    op.drop_table("clothes_tpo")
    op.drop_table("usage_logs")
    op.drop_table("subscriptions")
    op.drop_table("outfits")
    op.drop_table("clothes")
    op.drop_table("users")
