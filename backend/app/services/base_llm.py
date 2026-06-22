from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from app.services.usage import LlmUsage

StructuredResponseT = TypeVar("StructuredResponseT", bound=BaseModel)


class LLMStructuredResponseError(Exception):
    """構造化レスポンスの失敗（refusal / parse 失敗）。

    失敗した呼び出しも token を消費しているため、取得できていれば `usage` を
    載せて上位へ伝え、コスト集計（llm_usage_logs）から漏らさないようにする。
    """

    def __init__(self, message: str, *, usage: LlmUsage | None = None) -> None:
        super().__init__(message)
        self.usage = usage


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        *,
        response_format: type[StructuredResponseT],
    ) -> tuple[StructuredResponseT, LlmUsage | None]:
        """構造化レスポンスと token 使用量（取得不可なら None）を返す。"""
        pass
