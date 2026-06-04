from pathlib import Path

from openai import APIError
from app.api.v1.schemas.clothes import ClothingItem
from app.services.llm_client import get_llm_client

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "outfit_suggest.md"
try:
    _PROMPT_TEMPLATE: str = _PROMPT_PATH.read_text(encoding="utf-8")
except OSError as exc:
    raise RuntimeError(
        f"outfit_suggest.md が見つかりません: {_PROMPT_PATH}"
    ) from exc


class OutfitSuggestionError(Exception):
    pass


class OutfitService:
    def __init__(self):
        self.llm = get_llm_client()

    async def suggest(
        self,
        *,
        tpo: str,
        clothes: list[ClothingItem],
        weather: dict,
    ) -> str:
        clothes_summary = self._format_clothes(clothes)
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
            return await self.llm.generate(prompt)
        except APIError as exc:
            raise OutfitSuggestionError("failed to generate outfit suggestion") from exc

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
