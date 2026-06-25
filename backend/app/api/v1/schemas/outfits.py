import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.api.v1.schemas.clothes import ClothingItem

ClosetMode = Literal["owned", "free"]
DEFAULT_CLOSET_MODE: ClosetMode = "owned"


class OutfitSuggestRequest(BaseModel):
    tpo: str = Field(min_length=1, max_length=100)
    # NOTE: date は現状未使用（将来の指定日提案用の予約フィールド）
    date: str | None = Field(default=None, max_length=10)
    region_code: str | None = Field(default=None, max_length=10)
    clothing_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)
    exclude_clothing_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)


# --- 保存済みコーデ（GET /outfits, GET/PATCH /outfits/{id}）用スキーマ ---
# 手持ち（owned）／補完（suggested）が混在しうるため、suggest のレスポンス item と
# 形状を統一する（手持ちは clothing_item を解決、補完は clothing_item=null）。
class SuggestedOutfitItem(BaseModel):
    name: str
    role: str
    color: str | None = None
    pattern: str | None = None
    display_order: int
    clothing_item: ClothingItem | None = None


class SuggestedOutfit(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tpo: str
    region_code: str
    weather_summary: str | None = None
    weather_temp_max: float | None = None
    weather_temp_min: float | None = None
    comment: str | None = None
    coordinate_image_url: str | None = None
    is_favorite: bool = False
    source: str
    items: list[SuggestedOutfitItem]
    created_at: datetime


class OutfitsListResponse(BaseModel):
    items: list[SuggestedOutfit]
    total: int


# --- 保存（POST /outfits）/ 更新（PATCH /outfits/{id}）リクエスト ---
# FE は suggest レスポンスの item から clothes_id = clothing_item?.id ?? null を送る。
class OutfitCreateItem(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=20)
    color: str | None = Field(default=None, max_length=50)
    pattern: str | None = Field(default=None, max_length=20)
    display_order: int = Field(ge=0)
    clothes_id: uuid.UUID | None = None


class OutfitCreateRequest(BaseModel):
    tpo: str = Field(min_length=1, max_length=20)
    region_code: str = Field(min_length=1, max_length=5)
    comment: str | None = None
    is_favorite: bool = False
    items: list[OutfitCreateItem] = Field(min_length=1, max_length=20)


class OutfitUpdateRequest(BaseModel):
    is_favorite: bool


# --- LLM 提案（POST /outfits/suggest）用スキーマ ---
# 手持ち服はそのまま clothing_item に解決し、手持ちにない補完アイテムは
# clothing_item=null（name/role/color/pattern のみ）で返すハイブリッド形式。
# 現状は DB に保存しないため、id / created_at はレスポンス用に一時生成する。
class SuggestOutfitItem(BaseModel):
    name: str
    role: str
    color: str | None = None
    pattern: str | None = None
    display_order: int
    clothing_item: ClothingItem | None = None


class SuggestOutfit(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tpo: str
    region_code: str
    comment: str | None = None
    is_favorite: bool = False
    items: list[SuggestOutfitItem]
    created_at: datetime


class OutfitSuggestResponse(BaseModel):
    outfits: list[SuggestOutfit]
