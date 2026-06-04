import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.api.v1.schemas.clothes import ClothingItem
from app.api.v1.schemas.regions import Region


class OutfitSuggestRequest(BaseModel):
    tpo: str
    date: str | None = None
    region_code: str | None = None
    clothing_ids: list[uuid.UUID] = Field(default_factory=list)
    exclude_clothing_ids: list[uuid.UUID] = Field(default_factory=list)


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
    is_favorite: bool = False
    source: str
    items: list[SuggestedOutfitItem]
    created_at: datetime


class OutfitSuggestResponse(BaseModel):
    outfits: list[SuggestedOutfit]
    weather_summary: str
    region_used: Region
    cached: bool
