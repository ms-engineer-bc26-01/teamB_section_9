import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.api.v1.schemas.clothes import ClothingItem


class OutfitSuggestRequest(BaseModel):
    tpo: str = Field(min_length=1, max_length=100)
    date: str | None = Field(default=None, max_length=10)
    region_code: str | None = Field(default=None, max_length=10)
    clothing_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)
    exclude_clothing_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)


class SuggestedGeneratedOutfitItem(BaseModel):
    name: str
    role: str
    color: str | None
    pattern: str | None
    display_order: int
    clothing_item: ClothingItem | None = None


class SuggestedGeneratedOutfit(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tpo: str
    comment: str | None = None
    is_favorite: bool = False
    items: list[SuggestedGeneratedOutfitItem]
    created_at: datetime


class SuggestedOutfitItem(BaseModel):
    clothes_id: uuid.UUID
    role: str
    display_order: int
    clothing_item: ClothingItem


class SuggestedOutfit(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tpo: str
    region_code: str
    weather_summary: str
    weather_temp_max: float | None = None
    weather_temp_min: float | None = None
    comment: str | None = None
    coordinate_image_url: str | None = None
    is_favorite: bool = False
    source: str
    items: list[SuggestedOutfitItem]
    created_at: datetime


class OutfitSuggestResponse(BaseModel):
    outfits: list[SuggestedGeneratedOutfit]


class OutfitsListResponse(BaseModel):
    items: list[SuggestedOutfit]
    total: int
