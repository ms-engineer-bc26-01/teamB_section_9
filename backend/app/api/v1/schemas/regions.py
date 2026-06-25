from pydantic import BaseModel

from app.constants.regions import RegionInfo, get_region


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


def build_region_schema(code: str, info: RegionInfo) -> Region:
    """地域コードと地域マスタ情報から Region スキーマを組み立てる。"""
    return Region(
        code=code,
        prefecture_code=code.split("_")[0],
        prefecture_name=info["prefecture"],
        name=info["name"],
        city=info["city"],
        latitude=info["lat"],
        longitude=info["lng"],
    )


def to_region_schema(region_code: str) -> Region | None:
    """地域コードから Region スキーマを解決する。未定義コードは None。"""
    info = get_region(region_code)
    return build_region_schema(region_code, info) if info is not None else None
