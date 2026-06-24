import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ClothingCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=20)
    color: str | None = Field(default=None, max_length=50)
    pattern: str | None = Field(default=None, max_length=20)
    size: str | None = Field(default=None, max_length=50)
    season: list[str] = Field(default_factory=list)
    tpo_tags: list[str] = Field(default_factory=list)
    image_url: str | None = Field(default=None, min_length=1, max_length=512)
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


class ClothingUploadUrlRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: Literal["image/jpeg", "image/png", "image/webp"]


class UploadUrlResponse(BaseModel):
    upload_url: str = Field(min_length=1, max_length=2048)
    storage_path: str = Field(min_length=1, max_length=512)
    # FE が PUT 後に POST /clothes の image_url としてそのまま保存・表示できる公開 URL。
    # BE 側で組み立てるため FE はバケット名・パス構造を持たなくてよい（#133）。
    # max_length は保存側（ClothingCreateRequest）・DB（String(512)）と揃える。
    # storage_path・公開URL とも BE 生成の uuid パス（実値 ~160字）で 512 に達しない。
    image_url: str = Field(min_length=1, max_length=512)
