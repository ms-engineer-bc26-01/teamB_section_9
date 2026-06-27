from fastapi import APIRouter, Query

from app.api.v1.schemas.regions import Region, RegionsResponse, build_region_schema
from app.constants.regions import REGIONS, RegionInfo, get_regions_by_prefecture

router = APIRouter(prefix="/regions", tags=["Region"])


def _serialize_regions(regions: dict[str, RegionInfo]) -> list[Region]:
    return [build_region_schema(code, info) for code, info in regions.items()]


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
