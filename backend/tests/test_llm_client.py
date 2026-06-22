from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services import llm_client
from app.services.base_llm import LLMStructuredResponseError


def test_get_llm_client_returns_openai_client_for_openai_provider(monkeypatch) -> None:
    class FakeOpenAIClient:
        pass

    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")

    from app.services import openai_client

    monkeypatch.setattr(openai_client, "OpenAIClient", FakeOpenAIClient)

    client = llm_client.get_llm_client()

    assert isinstance(client, FakeOpenAIClient)


def test_get_llm_client_raises_for_unsupported_provider(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "claude")

    with pytest.raises(ValueError, match="Unsupported LLM provider: claude"):
        llm_client.get_llm_client()


def test_openai_client_requires_api_key(monkeypatch) -> None:
    from app.services.openai_client import OpenAIClient

    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)

    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required when LLM_PROVIDER is openai",
    ):
        OpenAIClient()


@pytest.mark.asyncio
async def test_openai_client_generates_structured_output(monkeypatch) -> None:
    from pydantic import BaseModel, ConfigDict

    from app.services.openai_client import OpenAIClient

    class Item(BaseModel):
        model_config = ConfigDict(extra="forbid")

        name: str
        category: str
        color: str | None
        pattern: str | None

    class Payload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        comment: str
        items: list[Item]

    class FakeResponses:
        async def parse(self, *, model: str, input: str, text_format):
            assert model == "gpt-test"
            assert input == "prompt"
            assert text_format is Payload
            return type(
                "FakeResponse",
                (),
                {
                    "output_parsed": Payload(
                        comment="ポイント",
                        items=[
                            Item(
                                name="白いリネンシャツ",
                                category="トップス",
                                color="白",
                                pattern="無地",
                            )
                        ],
                    ),
                    "output": [],
                },
            )()

    class FakeAsyncOpenAI:
        def __init__(self, *, api_key: str):
            assert api_key == "test-key"
            self.responses = FakeResponses()

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr("app.services.openai_client.AsyncOpenAI", FakeAsyncOpenAI)

    client = OpenAIClient()
    payload, usage = await client.generate_structured("prompt", response_format=Payload)

    assert payload.comment == "ポイント"
    assert payload.items[0].name == "白いリネンシャツ"
    # レスポンスに usage が無い場合は None（best-effort）
    assert usage is None


@pytest.mark.asyncio
async def test_openai_client_raises_on_structured_output_refusal(monkeypatch) -> None:
    from pydantic import BaseModel, ConfigDict

    from app.services.openai_client import OpenAIClient

    class Payload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        comment: str
        items: list[dict]

    refusal_content = type(
        "RefusalContent",
        (),
        {"type": "refusal", "refusal": "cannot comply"},
    )()
    message_output = type(
        "MessageOutput",
        (),
        {"type": "message", "content": [refusal_content]},
    )()

    class FakeResponses:
        async def parse(self, *, model: str, input: str, text_format):
            del model, input, text_format
            return type(
                "FakeResponse",
                (),
                {
                    "output_parsed": None,
                    "output": [message_output],
                    # refusal でも token は消費済み。usage が載っていることを模す。
                    "usage": SimpleNamespace(
                        input_tokens=7, output_tokens=0, total_tokens=7
                    ),
                },
            )()

    class FakeAsyncOpenAI:
        def __init__(self, *, api_key: str):
            del api_key
            self.responses = FakeResponses()

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr("app.services.openai_client.AsyncOpenAI", FakeAsyncOpenAI)

    client = OpenAIClient()

    with pytest.raises(LLMStructuredResponseError, match="cannot comply") as exc_info:
        await client.generate_structured("prompt", response_format=Payload)

    # 失敗時も消費 token を取りこぼさないよう、例外に usage を載せて伝える
    assert exc_info.value.usage is not None
    assert exc_info.value.usage.op == "generate_structured"
    assert exc_info.value.usage.total_tokens == 7


@pytest.mark.asyncio
async def test_generate_structured_logs_token_usage(monkeypatch, caplog) -> None:
    # client → log_llm_usage の結線回帰テスト。
    # generate_structured が usage 付きレスポンスから usage ログを出すことを保証する。
    import logging

    from pydantic import BaseModel, ConfigDict

    from app.services.openai_client import OpenAIClient

    class Payload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        comment: str

    class FakeResponses:
        async def parse(self, *, model: str, input: str, text_format):
            del model, input, text_format
            return type(
                "FakeResponse",
                (),
                {
                    "output_parsed": Payload(comment="ok"),
                    "output": [],
                    "usage": SimpleNamespace(
                        input_tokens=11,
                        output_tokens=22,
                        total_tokens=33,
                    ),
                },
            )()

    class FakeAsyncOpenAI:
        def __init__(self, *, api_key: str):
            del api_key
            self.responses = FakeResponses()

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr("app.services.openai_client.AsyncOpenAI", FakeAsyncOpenAI)

    client = OpenAIClient()

    with caplog.at_level(logging.INFO, logger="climo"):
        _, usage = await client.generate_structured("prompt", response_format=Payload)

    assert "llm_usage" in caplog.text
    assert "op=generate_structured" in caplog.text
    assert "model=gpt-test" in caplog.text
    assert "total_tokens=33" in caplog.text
    # 永続化のため呼び出し側へ usage を返すこと（戻り値配管の回帰）
    assert usage is not None
    assert usage.op == "generate_structured"
    assert usage.model == "gpt-test"
    assert usage.input_tokens == 11
    assert usage.output_tokens == 22
    assert usage.total_tokens == 33
