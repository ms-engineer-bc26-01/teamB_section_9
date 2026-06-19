"""OpenAI 呼び出しの token 使用量を計測・記録するユーティリティ。

各クライアント（テキスト/画像生成）から OpenAI レスポンスの `usage` を渡し、
構造化ログに出力してコストを確認可能にする。Responses API・Images API いずれの
usage（input_tokens / output_tokens / total_tokens）も同じ getattr で拾える。

NOTE: 永続集計（UsageLog テーブルへの保存）は user_id をクライアント層まで
渡す配管と token カラム追加マイグレーションが必要なため、後続タスクとする。
"""

from typing import Any

from app.core.logging import logger


def log_llm_usage(*, op: str, model: str, usage: Any | None) -> None:
    """OpenAI レスポンスの usage を構造化ログに出力する。

    出力するのは LLM 呼び出し種別（op）・モデル名・token 数のみ。prompt や
    response 本文・ユーザー識別情報は意図的に受け取らず、機微情報がログに
    混入しない（出力フィールドは allowlist 固定）。

    `op` は LLM 呼び出し種別（generate / generate_structured / generate_image）。
    レート制限・分析用の `usage_logs.action`（suggest_outfit 等のドメイン操作）
    とは別概念なのでキー名を分けている。

    usage が None（取得不可）の場合は何もしない（best-effort）。欠損フィールドは
    `None` のまま出力し、`total_tokens` をこちらで計算で埋めることはしない。
    """
    if usage is None:
        return

    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    logger.info(
        "llm_usage op=%s model=%s input_tokens=%s output_tokens=%s total_tokens=%s",
        op,
        model,
        input_tokens,
        output_tokens,
        total_tokens,
    )
