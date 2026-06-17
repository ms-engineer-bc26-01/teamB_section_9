import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Outfit(Base):
    __tablename__ = "outfits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    tpo: Mapped[str] = mapped_column(String(20), nullable=False)
    region_code: Mapped[str] = mapped_column(String(5), nullable=False)
    # 保存フロー（オンデマンド）では天気要約を持たないため nullable
    weather_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    weather_temp_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_temp_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    coordinate_image_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user = relationship("User", back_populates="outfits")
    items = relationship(
        "OutfitItem",
        back_populates="outfit",
        cascade="all, delete-orphan",
    )


class OutfitItem(Base):
    __tablename__ = "outfit_items"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('owned', 'suggested')",
            name="ck_outfit_items_source_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    outfit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("outfits.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 手持ち服のときのみ設定。補完提案（非手持ち）は NULL。
    # 服削除時は履歴を残すため SET NULL（表示は item_snapshot で継続）。
    clothes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clothes.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    # owned: 手持ち服 / suggested: LLM 補完アイテム
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 表示用スナップショット {name, color, pattern}。owned/suggested とも保存する
    # （owned は DB 値、suggested は入力値）。服削除後の履歴表示にも使う。
    item_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    outfit = relationship("Outfit", back_populates="items")
    clothes = relationship("Clothes", back_populates="outfit_items")
