import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClothingCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=20)
    color: str | None = Field(default=None, max_length=50)
    pattern: str | None = Field(default=None, max_length=20)
    size: str | None = Field(default=None, max_length=50)
    season: list[str] = Field(default_factory=list)
    tpo_tags: list[str] = Field(default_factory=list)
    image_url: str | None = Field(default=None, max_length=512)
    thumbnail_url: str | None = Field(default=None, max_length=512)
    memo: str | None = Field(default=None, max_length=200)
    is_favorite: bool = False


class ClothingUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=20)
    color: str | None = Field(default=None, max_length=50)
    pattern: str | None = Field(default=None, max_length=20)
    size: str | None = Field(default=None, max_length=50)
    season: list[str] | None = None
    tpo_tags: list[str] | None = None
    image_url: str | None = Field(default=None, min_length=1, max_length=512)
    thumbnail_url: str | None = Field(default=None, max_length=512)
    memo: str | None = Field(default=None, max_length=200)
    is_favorite: bool | None = None
    wear_count: int | None = Field(default=None, ge=0)
    last_worn_at: datetime | None = None


class ClothingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    category: str
    color: str | None
    pattern: str | None
    size: str | None
    season: list[str]
    tpo_tags: list[str]
    image_url: str | None
    thumbnail_url: str | None
    memo: str | None
    is_favorite: bool
    wear_count: int
    last_worn_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ClothesListResponse(BaseModel):
    items: list[ClothingItem]
    total: int
