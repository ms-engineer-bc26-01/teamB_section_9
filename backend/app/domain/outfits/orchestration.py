import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.outfits import (
    DEFAULT_CLOSET_MODE,
    ClosetMode,
    OutfitCreateItem,
    SuggestedOutfit,
)
from app.constants.regions import get_region
from app.core.logging import logger
from app.domain.clothes import crud as clothes_crud
from app.domain.outfits import crud as outfits_crud
from app.domain.outfits.image_service import generate_coordinate_image_url
from app.domain.outfits.service import (
    OutfitService,
    OutfitSuggestionError,
    SuggestedOutfitItemResult,
)
from app.domain.usage.crud import record_llm_usage
from app.services.usage import LlmUsage
from app.services.weather_client import (
    WeatherForecastResponseError,
    extract_outfit_prompt_weather,
    fetch_weather_forecast_cached,
)

DEFAULT_REGION_CODE = "13_01"
CLOTHES_FETCH_LIMIT = 1000
DEFAULT_BATCH_TPO = "business"


class InvalidRegionCodeError(Exception):
    """指定地域コードが未定義。"""


class OutfitWeatherError(Exception):
    """天気取得または整形に失敗した。"""


@dataclass(frozen=True, slots=True)
class OutfitSuggestionPlan:
    user_id: uuid.UUID
    tpo: str
    region_code: str
    comment: str
    items: list[SuggestedOutfitItemResult]
    usage: LlmUsage | None = None


async def persist_llm_usage_best_effort(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    usage: LlmUsage | None,
) -> None:
    """token 使用量をコスト観測用に best-effort で永続化する。"""
    try:
        await record_llm_usage(db, user_id=user_id, usage=usage)
    except Exception as exc:  # noqa: BLE001 - 永続化失敗を呼び出し元へ波及させない
        await db.rollback()
        logger.warning("failed to persist llm usage (user=%s): %s", user_id, exc)


def resolve_region_code(
    *,
    region_code: str | None,
    default_region_code: str | None,
) -> str:
    return region_code or default_region_code or DEFAULT_REGION_CODE


async def build_outfit_suggestion_plan(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    default_region_code: str | None,
    tpo: str,
    region_code: str | None = None,
    closet_mode: ClosetMode = DEFAULT_CLOSET_MODE,
    clothing_ids: list[uuid.UUID] | None = None,
    exclude_clothing_ids: list[uuid.UUID] | None = None,
) -> OutfitSuggestionPlan:
    resolved_region_code = resolve_region_code(
        region_code=region_code,
        default_region_code=default_region_code,
    )
    region = get_region(resolved_region_code)
    if region is None:
        raise InvalidRegionCodeError("invalid region_code")

    latitude, longitude = region["lat"], region["lng"]

    try:
        weather = await fetch_weather_forecast_cached(
            region_code=resolved_region_code,
            latitude=latitude,
            longitude=longitude,
            days=3,
        )
        prompt_weather = extract_outfit_prompt_weather(weather)
    except (httpx.HTTPError, WeatherForecastResponseError) as exc:
        logger.error(
            "weather fetch failed for outfit suggestion (user=%s, region=%s): %s",
            user_id,
            resolved_region_code,
            exc,
        )
        raise OutfitWeatherError("failed to fetch weather forecast") from exc

    if closet_mode == "owned":
        clothes = (
            await clothes_crud.list_clothes(
                db,
                user_id,
                limit=CLOTHES_FETCH_LIMIT,
                offset=0,
            )
        ).items
    else:
        clothes = []

    try:
        result = await OutfitService().suggest(
            tpo=tpo,
            clothes=clothes,
            weather=prompt_weather,
            closet_mode=closet_mode,
            clothing_ids=clothing_ids,
            exclude_clothing_ids=exclude_clothing_ids,
        )
    except OutfitSuggestionError as exc:
        logger.error(
            "outfit suggestion failed (user=%s, tpo=%s): %s",
            user_id,
            tpo,
            exc,
        )
        await persist_llm_usage_best_effort(db, user_id=user_id, usage=exc.usage)
        raise

    await persist_llm_usage_best_effort(db, user_id=user_id, usage=result.usage)

    logger.info(
        "outfit suggested (user=%s, region=%s, items=%d)",
        user_id,
        resolved_region_code,
        len(result.items),
    )

    return OutfitSuggestionPlan(
        user_id=user_id,
        tpo=tpo,
        region_code=resolved_region_code,
        comment=result.comment,
        items=result.items,
        usage=result.usage,
    )


async def save_outfit_from_plan(
    db: AsyncSession,
    *,
    plan: OutfitSuggestionPlan,
    is_favorite: bool = False,
) -> SuggestedOutfit:
    return await outfits_crud.create_outfit(
        db,
        user_id=plan.user_id,
        tpo=plan.tpo,
        region_code=plan.region_code,
        comment=plan.comment,
        is_favorite=is_favorite,
        items=[
            OutfitCreateItem(
                name=item.name,
                role=item.role,
                color=item.color,
                pattern=item.pattern,
                display_order=item.display_order,
                clothes_id=item.clothing_item.id if item.clothing_item else None,
            )
            for item in plan.items
        ],
    )


async def generate_coordinate_image_for_outfit(
    db: AsyncSession,
    *,
    outfit: SuggestedOutfit,
) -> SuggestedOutfit:
    url, usage = await generate_coordinate_image_url(
        outfit_id=outfit.id,
        comment=outfit.comment,
        items=outfit.items,
    )
    await persist_llm_usage_best_effort(db, user_id=outfit.user_id, usage=usage)
    if url is None:
        return outfit

    updated = await outfits_crud.set_coordinate_image_url(
        db,
        outfit.user_id,
        outfit.id,
        coordinate_image_url=url,
    )
    if updated is None:
        logger.warning(
            "coordinate image generated but outfit not found for update "
            "(outfit=%s, user=%s)",
            outfit.id,
            outfit.user_id,
        )
        return outfit
    return updated


async def generate_outfit_for_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    default_region_code: str | None,
    tpo: str = DEFAULT_BATCH_TPO,
    region_code: str | None = None,
    closet_mode: ClosetMode = DEFAULT_CLOSET_MODE,
    is_favorite: bool = False,
) -> SuggestedOutfit:
    """コーデ提案を保存し、画像生成は best-effort で後続適用した結果を返す。

    画像生成や Storage 保存に失敗した場合でもコーデ本体は保存され、
    返却値の coordinate_image_url は None のままになり得る。
    """
    plan = await build_outfit_suggestion_plan(
        db,
        user_id=user_id,
        default_region_code=default_region_code,
        tpo=tpo,
        region_code=region_code,
        closet_mode=closet_mode,
    )
    saved = await save_outfit_from_plan(db, plan=plan, is_favorite=is_favorite)
    return await generate_coordinate_image_for_outfit(db, outfit=saved)
