from pathlib import Path

from app.services.llm_client import get_llm_client

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "outfit_suggest.md"


class OutfitService:
    def __init__(self):
        self.llm = get_llm_client()

    async def suggest(
        self,
        clothes: list[str],
        weather: str,
    ) -> str:

        prompt = (
            PROMPT_PATH.read_text(encoding="utf-8")
            .replace(
                "{{ clothes }}",
                ", ".join(clothes),
            )
            .replace(
                "{{ weather }}",
                weather,
            )
        )

        return await self.llm.generate(prompt)
