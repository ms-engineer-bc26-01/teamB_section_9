from dataclasses import dataclass
from pathlib import Path

from openai import APIError

from app.api.v1.schemas.clothes import ClothingItem
from app.services.llm_client import get_llm_client

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "outfit_suggest.md"
try:
    _PROMPT_TEMPLATE: str = _PROMPT_PATH.read_text(encoding="utf-8")
except OSError as exc:
    raise RuntimeError(f"outfit_suggest.md が見つかりません: {_PROMPT_PATH}") from exc


class OutfitSuggestionError(Exception):
    pass


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
    ) -> "OutfitSuggestion":
        selected = self._select_clothes(tpo=tpo, clothes=clothes)
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
            comment = await self.llm.generate(prompt)
        except APIError as exc:
            raise OutfitSuggestionError("failed to generate outfit suggestion") from exc

        return OutfitSuggestion(
            comment=comment.strip(),
            weather_summary=weather_summary,
            items=selected,
        )

    @staticmethod
    def _select_clothes(
        *,
        tpo: str,
        clothes: list[ClothingItem],
    ) -> list["SuggestedClothingSelection"]:
        selected: list[SuggestedClothingSelection] = []
        selected_ids: set = set()
        display_order = 1

        for category in ("outer", "tops", "bottoms", "shoes", "bag", "accessory"):
            candidates = [
                item
                for item in clothes
                if item.category == category and item.id not in selected_ids
            ]
            if not candidates:
                continue

            best_item = max(
                candidates, key=lambda item: OutfitService._score_item(item, tpo)
            )
            selected.append(
                SuggestedClothingSelection(
                    clothing_item=best_item,
                    role=category,
                    display_order=display_order,
                )
            )
            selected_ids.add(best_item.id)
            display_order += 1

        return selected

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
