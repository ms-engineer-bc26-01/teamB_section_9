from fastapi import APIRouter, Query

from app.api.v1.schemas.regions import Region, RegionsResponse
from app.constants.regions import REGIONS, get_regions_by_prefecture

router = APIRouter(prefix="/regions", tags=["Region"])


def _serialize_regions(regions: dict[str, dict[str, str | float]]) -> list[Region]:
    return [
        Region(
            code=code,
            prefecture_code=code.split("_")[0],
            prefecture_name=info["prefecture"],
            name=info["name"],
            city=info["city"],
            latitude=info["lat"],
            longitude=info["lng"],
        )
        for code, info in regions.items()
    ]


@router.get("", response_model=RegionsResponse)
async def list_regions(
    prefecture_code: str | None = Query(default=None, pattern=r"^[0-9]{2}$"),
) -> RegionsResponse:
    regions = (
        REGIONS
        if prefecture_code is None
        else get_regions_by_prefecture(prefecture_code)
    )
    return RegionsResponse(items=_serialize_regions(regions))
