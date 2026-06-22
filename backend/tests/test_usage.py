import logging
from types import SimpleNamespace

from app.services.usage import extract_llm_usage, log_llm_usage


def test_log_llm_usage_emits_tokens(caplog):
    # Arrange
    usage = SimpleNamespace(input_tokens=120, output_tokens=45, total_tokens=165)

    # Act
    with caplog.at_level(logging.INFO, logger="climo"):
        log_llm_usage(op="generate_structured", model="gpt-5", usage=usage)

    # Assert
    record = caplog.text
    assert "llm_usage" in record
    assert "op=generate_structured" in record
    assert "model=gpt-5" in record
    assert "input_tokens=120" in record
    assert "output_tokens=45" in record
    assert "total_tokens=165" in record


def test_log_llm_usage_noop_when_usage_none(caplog):
    # Arrange / Act
    with caplog.at_level(logging.INFO, logger="climo"):
        log_llm_usage(op="generate", model="gpt-5", usage=None)

    # Assert: usage が無ければ何も記録しない
    assert "llm_usage" not in caplog.text


def test_log_llm_usage_handles_missing_fields(caplog):
    # Arrange: 一部フィールドが欠ける usage でも例外を出さない
    usage = SimpleNamespace(total_tokens=10)

    # Act
    with caplog.at_level(logging.INFO, logger="climo"):
        log_llm_usage(op="generate_image", model="gpt-image-1", usage=usage)

    # Assert
    assert "total_tokens=10" in caplog.text
    assert "input_tokens=None" in caplog.text


def test_log_llm_usage_does_not_leak_prompt_or_response(caplog):
    # Arrange: usage 以外の本文（prompt/response）を持つオブジェクトを渡しても
    #          ログには token 数しか出力されないことを保証する（allowlist）。
    usage = SimpleNamespace(
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        # 本来 usage には無いが、誤って混入しても拾われないことの番兵
        prompt="SECRET_PROMPT_BODY",
        response="SECRET_RESPONSE_BODY",
    )

    # Act
    with caplog.at_level(logging.INFO, logger="climo"):
        log_llm_usage(op="generate", model="gpt-5", usage=usage)

    # Assert
    assert "SECRET_PROMPT_BODY" not in caplog.text
    assert "SECRET_RESPONSE_BODY" not in caplog.text


def test_extract_llm_usage_returns_normalized_dataclass():
    # Arrange
    usage = SimpleNamespace(input_tokens=11, output_tokens=22, total_tokens=33)

    # Act
    result = extract_llm_usage(op="generate_structured", model="gpt-5", usage=usage)

    # Assert
    assert result is not None
    assert result.op == "generate_structured"
    assert result.model == "gpt-5"
    assert result.input_tokens == 11
    assert result.output_tokens == 22
    assert result.total_tokens == 33


def test_extract_llm_usage_returns_none_when_usage_none():
    assert extract_llm_usage(op="generate", model="gpt-5", usage=None) is None


def test_extract_llm_usage_keeps_missing_fields_as_none():
    # Arrange: 一部フィールドが欠ける usage は None のまま保持（計算で埋めない）
    usage = SimpleNamespace(total_tokens=10)

    # Act
    result = extract_llm_usage(op="generate_image", model="gpt-image-1", usage=usage)

    # Assert
    assert result is not None
    assert result.total_tokens == 10
    assert result.input_tokens is None
    assert result.output_tokens is None
