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
from app.domain.usage.crud import record_llm_usage
from app.services.image_client import ImageGenerationError, OpenAIImageClient
from app.services.image_prompt_builder import OutfitItemLike, build_image_prompt
from app.services.storage_client import StorageError, upload_image
from app.services.usage import LlmUsage


async def generate_coordinate_image_url(
    *,
    outfit_id: uuid.UUID,
    comment: str | None,
    items: Sequence[OutfitItemLike],
) -> tuple[str | None, LlmUsage | None]:
    """コーデ内容からコラージュ画像を生成・保存し、公開 URL と token 使用量を返す。

    失敗時（API キー未設定・生成エラー・アップロード失敗など）は警告ログを残して
    URL に None を返す。呼び出し側はこの None を coordinate_image_url 未設定として扱う。
    画像生成自体が成功していれば、アップロード失敗時でも usage は返す
    （生成で token を消費しているため）。生成前の失敗では usage は None。
    """
    phase = "prompt_build"
    usage: LlmUsage | None = None
    try:
        prompt = build_image_prompt(comment, items)
        phase = "image_generate"
        client = OpenAIImageClient()
        data, usage = await client.generate_image(prompt)
        phase = "storage_upload"
        url = await upload_image(path=f"outfits/{outfit_id}.png", data=data)
        return url, usage
    except (ImageGenerationError, StorageError, ValueError) as exc:
        # best-effort: 失敗フェーズと例外種別を残し、後から観測できるようにする。
        logger.warning(
            "coordinate image generation skipped (outfit=%s, phase=%s, error=%s): %s",
            outfit_id,
            phase,
            type(exc).__name__,
            exc,
        )
        return None, usage


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

    NOTE: FastAPI の BackgroundTasks はアプリプロセス内の簡易非同期実行であり、
    **実行保証・再試行保証はない**（プロセス停止・デプロイ等で未完了になり得る／
    一度失敗した画像は自然回復しない）。永続化・リトライが必要になった場合は
    ジョブキュー（Celery / arq + Redis 等）への移行を検討する。
    """
    try:
        url, usage = await generate_coordinate_image_url(
            outfit_id=outfit_id,
            comment=comment,
            items=items,
        )
        if url is None and usage is None:
            return
        async with SessionLocal() as db:
            # token 使用量を best-effort で永続化（生成成功なら url が None でも残す）。
            # ここでの失敗は URL 保存をブロックしないよう独立して握りつぶす。
            try:
                await record_llm_usage(db, user_id=user_id, usage=usage)
            except Exception as exc:  # noqa: BLE001
                await db.rollback()
                logger.warning(
                    "failed to persist image llm usage (outfit=%s): %s",
                    outfit_id,
                    exc,
                )
            if url is None:
                return
            updated = await set_coordinate_image_url(
                db,
                user_id,
                outfit_id,
                coordinate_image_url=url,
            )
        # 生成中にコーデが削除される等で対象が見つからなかった場合は観測できるよう残す。
        if updated is None:
            logger.warning(
                "coordinate image generated but outfit not found for update "
                "(outfit=%s, user=%s)",
                outfit_id,
                user_id,
            )
    except Exception as exc:  # noqa: BLE001 - 背景タスクの失敗をリクエストに波及させない
        logger.warning(
            "background coordinate image task failed (outfit=%s): %s",
            outfit_id,
            exc,
        )
