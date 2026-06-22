"""LLM token 使用量の永続化 CRUD。

`llm_usage_logs` への insert を担う。永続化は best-effort（コスト観測目的であり、
失敗してもユーザーのリクエストを壊さない）。呼び出し側で try/except に包む。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.llm_usage_log import LlmUsageLog
from app.services.usage import LlmUsage


async def record_llm_usage(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    usage: LlmUsage | None,
) -> None:
    """1 回の LLM 呼び出しの token 使用量を 1 行 insert する。

    usage が None（取得不可）の場合は何もしない（no-op）。token フィールドは
    None のまま保存する（NULL 許容）。
    """
    if usage is None:
        return

    db.add(
        LlmUsageLog(
            user_id=user_id,
            op=usage.op,
            model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
        )
    )
    await db.commit()
