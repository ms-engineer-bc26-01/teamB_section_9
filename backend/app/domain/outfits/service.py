import uuid
from dataclasses import dataclass
from pathlib import Path

from openai import APIError
from pydantic import BaseModel, ConfigDict

from app.api.v1.schemas.clothes import ClothingItem
from app.services.base_llm import LLMStructuredResponseError
from app.services.llm_client import get_llm_client

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "outfit_suggest.md"
try:
    _PROMPT_TEMPLATE: str = _PROMPT_PATH.read_text(encoding="utf-8")
except OSError as exc:
    raise RuntimeError(f"outfit_suggest.md が見つかりません: {_PROMPT_PATH}") from exc


class OutfitSuggestionError(Exception):
    pass


class LLMOutfitSuggestionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    color: str | None
    pattern: str | None


class LLMOutfitSuggestionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str
    items: list[LLMOutfitSuggestionItem]


class OutfitService:
    def __init__(self):
        try:
            self.llm = get_llm_client()
        except ValueError as exc:
            raise OutfitSuggestionError("failed to generate outfit suggestion") from exc

    async def suggest(
        self,
        *,
        tpo: str,
        clothes: list[ClothingItem],
        weather: dict,
        clothing_ids: list[uuid.UUID] | None = None,
        exclude_clothing_ids: list[uuid.UUID] | None = None,
    ) -> "OutfitSuggestion":
        selected = self._select_clothes(
            tpo=tpo,
            clothes=clothes,
            clothing_ids=clothing_ids,
            exclude_clothing_ids=exclude_clothing_ids,
        )
        selected_clothes = [s.clothing_item for s in selected]

        clothes_summary = self._format_clothes(selected_clothes)
        weather_summary = self._format_weather(weather)

        prompt = (
            _PROMPT_TEMPLATE.replace(
                "{{ clothes }}",
                clothes_summary,
            )
            .replace(
                "{{ weather }}",
                weather_summary,
            )
            .replace(
                "{{ tpo }}",
                tpo,
            )
        )

        try:
            payload = await self.llm.generate_structured(
                prompt,
                response_format=LLMOutfitSuggestionPayload,
            )
        except (APIError, LLMStructuredResponseError) as exc:
            raise OutfitSuggestionError("failed to generate outfit suggestion") from exc

        return OutfitSuggestion(
            comment=payload.comment.strip(),
            weather_summary=weather_summary,
            items=selected,
        )

    @staticmethod
    def _select_clothes(
        *,
        tpo: str,
        clothes: list[ClothingItem],
        clothing_ids: list[uuid.UUID] | None = None,
        exclude_clothing_ids: list[uuid.UUID] | None = None,
    ) -> list["SuggestedClothingSelection"]:
        """コーデを構成する服を選定する。

        仕様 (Issue #61):
        - exclude_clothing_ids: その服を候補から完全に除外する（提案に出さない）。
        - clothing_ids: その服を必ず提案に含める（ユーザー指定を最優先）。
          同カテゴリ複数指定や onepiece と tops/bottoms の同時指定も、
          すべて結果に含める（通常の 1カテゴリ1点・onepiece 排他より優先）。
        - 指定で埋まらないカテゴリは、除外・指定済みを除いた手持ちから
          従来のスコア選定ロジックで自動補完する。
        - clothing_ids が（除外後の）手持ちに無い場合は含めようがないため無視する。
        """
        pool = clothes
        if exclude_clothing_ids:
            excluded = set(exclude_clothing_ids)
            pool = [c for c in pool if c.id not in excluded]

        forced_ids = set(clothing_ids or [])
        forced = [c for c in pool if c.id in forced_ids]
        forced_id_set = {c.id for c in forced}
        auto_pool = [c for c in pool if c.id not in forced_id_set]

        forced_by_category: dict[str, list[ClothingItem]] = {}
        for item in forced:
            forced_by_category.setdefault(item.category, []).append(item)

        selected: list[SuggestedClothingSelection] = []
        display_order = 1

        def add(item: ClothingItem, role: str) -> None:
            nonlocal display_order
            selected.append(
                SuggestedClothingSelection(
                    clothing_item=item,
                    role=role,
                    display_order=display_order,
                )
            )
            display_order += 1

        def best_of(category: str) -> ClothingItem | None:
            cands = [i for i in auto_pool if i.category == category]
            if not cands:
                return None
            return max(cands, key=lambda i: OutfitService._score_item(i, tpo))

        # outer
        if "outer" in forced_by_category:
            for item in forced_by_category["outer"]:
                add(item, "outer")
        else:
            best = best_of("outer")
            if best:
                add(best, "outer")

        # torso（onepiece か tops/bottoms）
        forced_onepiece = forced_by_category.get("onepiece", [])
        forced_tops = forced_by_category.get("tops", [])
        forced_bottoms = forced_by_category.get("bottoms", [])
        if forced_onepiece or forced_tops or forced_bottoms:
            for item in forced_onepiece:
                add(item, "onepiece")
            for item in forced_tops:
                add(item, "tops")
            for item in forced_bottoms:
                add(item, "bottoms")
            # onepiece 指定が無ければ tops/bottoms の欠けを自動補完
            if not forced_onepiece:
                if not forced_tops and (best := best_of("tops")):
                    add(best, "tops")
                if not forced_bottoms and (best := best_of("bottoms")):
                    add(best, "bottoms")
        else:
            torso = OutfitService._select_torso(
                tpo=tpo,
                clothes=auto_pool,
                selected_ids=set(),
            )
            for item, role in torso:
                add(item, role)

        # shoes / bag / accessory
        for category in ("shoes", "bag", "accessory"):
            if category in forced_by_category:
                for item in forced_by_category[category]:
                    add(item, category)
            elif best := best_of(category):
                add(best, category)

        # 上記以外のカテゴリで指定された服は末尾に含める（取りこぼし防止）
        handled = {"outer", "onepiece", "tops", "bottoms", "shoes", "bag", "accessory"}
        for item in forced:
            if item.category not in handled:
                add(item, item.category)

        return selected

    @staticmethod
    def _select_torso(
        *,
        tpo: str,
        clothes: list[ClothingItem],
        selected_ids: set,
    ) -> list[tuple[ClothingItem, str]]:
        tops_cands = [
            i for i in clothes if i.category == "tops" and i.id not in selected_ids
        ]
        btms_cands = [
            i for i in clothes if i.category == "bottoms" and i.id not in selected_ids
        ]
        one_cands = [
            i for i in clothes if i.category == "onepiece" and i.id not in selected_ids
        ]
        best_tops = (
            max(tops_cands, key=lambda i: OutfitService._score_item(i, tpo))
            if tops_cands
            else None
        )
        best_btms = (
            max(btms_cands, key=lambda i: OutfitService._score_item(i, tpo))
            if btms_cands
            else None
        )
        best_one = (
            max(one_cands, key=lambda i: OutfitService._score_item(i, tpo))
            if one_cands
            else None
        )

        if best_one:
            one_score = OutfitService._score_item(best_one, tpo)
            tb_scores = [
                OutfitService._score_item(i, tpo)
                for i in (best_tops, best_btms)
                if i is not None
            ]
            if not tb_scores or one_score > max(tb_scores):
                return [(best_one, "onepiece")]

        return [
            (item, role)
            for item, role in ((best_tops, "tops"), (best_btms, "bottoms"))
            if item
        ]

    @staticmethod
    def _score_item(item: ClothingItem, tpo: str) -> tuple[int, int, int, int]:
        return (
            1 if tpo in item.tpo_tags else 0,
            1 if item.is_favorite else 0,
            1 if "all" in item.season else 0,
            item.wear_count,
        )

    @staticmethod
    def _format_clothes(clothes: list[ClothingItem]) -> str:
        if not clothes:
            return "服の登録はありません。"

        lines = []
        for item in clothes:
            details = [item.category, item.name]
            if item.color:
                details.append(f"color={item.color}")
            if item.pattern:
                details.append(f"pattern={item.pattern}")
            if item.size:
                details.append(f"size={item.size}")
            if item.season:
                details.append(f"season={', '.join(item.season)}")
            if item.tpo_tags:
                details.append(f"tpo={', '.join(item.tpo_tags)}")
            if item.memo:
                details.append(f"memo={item.memo}")
            lines.append(" - ".join(details))

        return "\n".join(lines)

    @staticmethod
    def _format_weather(weather: dict) -> str:
        current = weather["current"]
        daily = weather["daily"]

        lines = [
            (
                "current: "
                f"temp={current['temperature_2m']}C, "
                f"weather_code={current['weather_code']}, "
                "precipitation_probability="
                f"{current['precipitation_probability']}%"
            )
        ]

        for forecast in daily:
            lines.append(
                (
                    f"{forecast['date']}: "
                    f"max={forecast['temperature_max']}C, "
                    f"min={forecast['temperature_min']}C, "
                    f"weather_code={forecast['weather_code']}, "
                    "precipitation_probability_max="
                    f"{forecast['precipitation_probability_max']}%"
                )
            )

        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class SuggestedClothingSelection:
    clothing_item: ClothingItem
    role: str
    display_order: int


@dataclass(frozen=True, slots=True)
class OutfitSuggestion:
    comment: str
    weather_summary: str
    items: list[SuggestedClothingSelection]
