"""コーデのコラージュ画像を生成して Storage に保存するオーケストレーション層。

PromptBuilder → 画像生成（OpenAI Image API）→ Supabase Storage アップロードを
束ね、公開 URL を返す。外部 I/O の失敗は **best-effort** として握りつぶし、
None を返す（コーデ保存自体は失敗させない方針）。
"""

import uuid
from collections.abc import Sequence

from app.core.logging import logger
from app.services.image_client import ImageGenerationError, OpenAIImageClient
from app.services.image_prompt_builder import OutfitItemLike, build_image_prompt
from app.services.storage_client import StorageError, upload_image


async def generate_coordinate_image_url(
    *,
    outfit_id: uuid.UUID,
    comment: str | None,
    items: Sequence[OutfitItemLike],
) -> str | None:
    """コーデ内容からコラージュ画像を生成・保存し、公開 URL を返す。

    失敗時（API キー未設定・生成エラー・アップロード失敗など）は警告ログを残して
    None を返す。呼び出し側はこの None を coordinate_image_url 未設定として扱う。
    """
    try:
        prompt = build_image_prompt(comment, items)
        client = OpenAIImageClient()
        data = await client.generate_image(prompt)
        return await upload_image(path=f"outfits/{outfit_id}.png", data=data)
    except (ImageGenerationError, StorageError, ValueError) as exc:
        logger.warning(
            "coordinate image generation skipped for outfit %s: %s", outfit_id, exc
        )
        return None
