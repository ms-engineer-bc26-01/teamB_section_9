import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Clothes(Base):
    __tablename__ = "clothes"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(20), nullable=True)
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    season: Mapped[list[str]] = mapped_column(ARRAY(String(20)), nullable=False)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    memo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    wear_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    last_worn_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="clothes")
    tpo_tags = relationship(
        "ClothesTpo",
        back_populates="clothes",
        cascade="all, delete-orphan",
    )
    outfit_items = relationship(
        "OutfitItem",
        back_populates="clothes",
        cascade="all, delete-orphan",
    )


class ClothesTpo(Base):
    __tablename__ = "clothes_tpo"

    clothes_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clothes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tpo_tag: Mapped[str] = mapped_column(String(20), primary_key=True)

    clothes = relationship("Clothes", back_populates="tpo_tags")
