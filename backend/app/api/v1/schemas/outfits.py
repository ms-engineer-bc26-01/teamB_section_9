import uuid

from pydantic import BaseModel, Field


class OutfitSuggestRequest(BaseModel):
    tpo: str
    date: str | None = None
    region_code: str | None = None
    clothing_ids: list[uuid.UUID] = Field(default_factory=list)
    exclude_clothing_ids: list[uuid.UUID] = Field(default_factory=list)


class OutfitSuggestResponse(BaseModel):
    coordinate: str
