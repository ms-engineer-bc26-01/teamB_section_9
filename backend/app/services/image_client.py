"""OpenAI Image API でコラージュ画像を生成するクライアント。

`openai_client.OpenAIClient`（テキスト生成）と対をなす画像生成サービス。
プロンプト文字列から画像バイト列（PNG）を生成して返す。例外は
`ImageGenerationError` に集約し、呼び出し側が best-effort で握れるようにする。
"""

import base64

from openai import APIError, AsyncOpenAI

from app.core.config import settings
from app.services.usage import LlmUsage, extract_llm_usage, log_llm_usage


class ImageGenerationError(Exception):
    """画像生成の失敗（API エラー・空レスポンス等）を表す。"""


class OpenAIImageClient:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for image generation")

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_IMAGE_TIMEOUT_SECONDS,
        )

    async def generate_image(self, prompt: str) -> tuple[bytes, LlmUsage | None]:
        """プロンプトから画像を生成し、PNG バイト列と token 使用量を返す。

        使用量は取得不可なら None（best-effort）。
        """
        try:
            response = await self.client.images.generate(
                model=settings.OPENAI_IMAGE_MODEL,
                prompt=prompt,
                n=1,
                size=settings.OPENAI_IMAGE_SIZE,
                quality=settings.OPENAI_IMAGE_QUALITY,
            )
        except APIError as exc:
            raise ImageGenerationError("failed to generate outfit image") from exc

        usage = getattr(response, "usage", None)
        log_llm_usage(
            op="generate_image",
            model=settings.OPENAI_IMAGE_MODEL,
            usage=usage,
        )
        llm_usage = extract_llm_usage(
            op="generate_image",
            model=settings.OPENAI_IMAGE_MODEL,
            usage=usage,
        )

        data = getattr(response, "data", None)
        if not data:
            raise ImageGenerationError("image generation returned no data")

        b64 = getattr(data[0], "b64_json", None)
        if not b64:
            raise ImageGenerationError("image generation returned no image content")

        try:
            return base64.b64decode(b64), llm_usage
        except (ValueError, TypeError) as exc:
            raise ImageGenerationError("failed to decode generated image") from exc
