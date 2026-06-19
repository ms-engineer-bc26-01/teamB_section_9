"""コーデのコラージュ画像を生成して Storage に保存するオーケストレーション層。

PromptBuilder → 画像生成（OpenAI Image API）→ Supabase Storage アップロードを
束ね、公開 URL を返す。外部 I/O の失敗は **best-effort** として握りつぶし、
None を返す（コーデ保存自体は失敗させない方針）。
"""

import uuid
from collections.abc import Sequence

from app.core.logging import logger
from app.db.session import SessionLocal
from app.domain.outfits.crud import set_coordinate_image_url
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
    phase = "prompt_build"
    try:
        prompt = build_image_prompt(comment, items)
        phase = "image_generate"
        client = OpenAIImageClient()
        data = await client.generate_image(prompt)
        phase = "storage_upload"
        return await upload_image(path=f"outfits/{outfit_id}.png", data=data)
    except (ImageGenerationError, StorageError, ValueError) as exc:
        # best-effort: 失敗フェーズと例外種別を残し、後から観測できるようにする。
        logger.warning(
            "coordinate image generation skipped (outfit=%s, phase=%s, error=%s): %s",
            outfit_id,
            phase,
            type(exc).__name__,
            exc,
        )
        return None


async def generate_and_store_coordinate_image(
    *,
    outfit_id: uuid.UUID,
    user_id: uuid.UUID,
    comment: str | None,
    items: Sequence[OutfitItemLike],
) -> None:
    """背景タスク用エントリポイント。

    画像生成（best-effort）を行い、成功した場合のみ **独自の DB セッション**で
    coordinate_image_url を保存する。背景タスクはレスポンス返却後に実行され、
    リクエストスコープの DB セッションは既に閉じているため、ここで SessionLocal から
    新しいセッションを開く。例外はリクエストへ波及しないよう必ずログ化して握りつぶす。
    """
    try:
        url = await generate_coordinate_image_url(
            outfit_id=outfit_id,
            comment=comment,
            items=items,
        )
        if url is None:
            return
        async with SessionLocal() as db:
            await set_coordinate_image_url(
                db,
                user_id,
                outfit_id,
                coordinate_image_url=url,
            )
    except Exception as exc:  # noqa: BLE001 - 背景タスクの失敗をリクエストに波及させない
        logger.warning(
            "background coordinate image task failed (outfit=%s): %s",
            outfit_id,
            exc,
        )
