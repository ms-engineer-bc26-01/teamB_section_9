import logging
from types import SimpleNamespace

from app.services.usage import log_llm_usage


def test_log_llm_usage_emits_tokens(caplog):
    # Arrange
    usage = SimpleNamespace(input_tokens=120, output_tokens=45, total_tokens=165)

    # Act
    with caplog.at_level(logging.INFO, logger="climo"):
        log_llm_usage(action="generate_structured", model="gpt-5", usage=usage)

    # Assert
    record = caplog.text
    assert "llm_usage" in record
    assert "action=generate_structured" in record
    assert "model=gpt-5" in record
    assert "input_tokens=120" in record
    assert "output_tokens=45" in record
    assert "total_tokens=165" in record


def test_log_llm_usage_noop_when_usage_none(caplog):
    # Arrange / Act
    with caplog.at_level(logging.INFO, logger="climo"):
        log_llm_usage(action="generate", model="gpt-5", usage=None)

    # Assert: usage が無ければ何も記録しない
    assert "llm_usage" not in caplog.text


def test_log_llm_usage_handles_missing_fields(caplog):
    # Arrange: 一部フィールドが欠ける usage でも例外を出さない
    usage = SimpleNamespace(total_tokens=10)

    # Act
    with caplog.at_level(logging.INFO, logger="climo"):
        log_llm_usage(action="generate_image", model="gpt-image-1", usage=usage)

    # Assert
    assert "total_tokens=10" in caplog.text
    assert "input_tokens=None" in caplog.text
