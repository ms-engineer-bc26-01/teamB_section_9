from pydantic import BaseModel


class OutfitSuggestRequest(BaseModel):
    clothes: list[str]
    weather: str


class OutfitSuggestResponse(BaseModel):
    coordinate: str
