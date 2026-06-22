"""OpenAI 呼び出しの token 使用量を計測・記録するユーティリティ。

各クライアント（テキスト/画像生成）から OpenAI レスポンスの `usage` を渡し、
構造化ログに出力してコストを確認可能にする。Responses API・Images API いずれの
usage（input_tokens / output_tokens / total_tokens）も同じ getattr で拾える。

`extract_llm_usage()` で usage を `LlmUsage` に正規化し、上位層（user_id + db を
持つ層）で DB 永続化（`llm_usage_logs`）できるようにする。stdout 構造化ログは
従来どおり `log_llm_usage()` で残す（永続化とは独立した best-effort）。
"""

from dataclasses import dataclass
from typing import Any

from app.core.logging import logger


@dataclass(frozen=True, slots=True)
class LlmUsage:
    """1 回の LLM 呼び出しの token 使用量。

    op は LLM 呼び出し種別（generate / generate_structured / generate_image）。
    token フィールドは取得不可なら None（こちらで total を計算で埋めない）。
    """

    op: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


def extract_llm_usage(*, op: str, model: str, usage: Any | None) -> LlmUsage | None:
    """OpenAI レスポンスの usage を `LlmUsage` に正規化する。

    usage が None（取得不可）なら None を返す（best-effort）。欠損フィールドは
    None のまま保持し、`total_tokens` をこちらで計算で埋めることはしない。
    """
    if usage is None:
        return None

    return LlmUsage(
        op=op,
        model=model,
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
    )


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
    extracted = extract_llm_usage(op=op, model=model, usage=usage)
    if extracted is None:
        return

    logger.info(
        "llm_usage op=%s model=%s input_tokens=%s output_tokens=%s total_tokens=%s",
        extracted.op,
        extracted.model,
        extracted.input_tokens,
        extracted.output_tokens,
        extracted.total_tokens,
    )
