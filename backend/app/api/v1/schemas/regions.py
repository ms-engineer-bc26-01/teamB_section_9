from pydantic import BaseModel


class Region(BaseModel):
    code: str
    prefecture_code: str
    prefecture_name: str
    name: str
    city: str
    latitude: float
    longitude: float


class RegionsResponse(BaseModel):
    items: list[Region]
