import uuid

import pytest

from app.db.models.llm_usage_log import LlmUsageLog
from app.domain.usage.crud import record_llm_usage
from app.services.usage import LlmUsage

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class _FakeSession:
    """add した行と commit 回数を記録する最小フェイク。"""

    def __init__(self):
        self.added: list = []
        self.commits = 0

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1


@pytest.mark.asyncio
async def test_record_llm_usage_inserts_row_with_tokens():
    # Arrange
    db = _FakeSession()
    usage = LlmUsage(
        op="generate_structured",
        model="gpt-5",
        input_tokens=11,
        output_tokens=22,
        total_tokens=33,
    )

    # Act
    await record_llm_usage(db, user_id=USER_ID, usage=usage)

    # Assert: token を含めて 1 行 insert + commit される
    assert len(db.added) == 1
    assert db.commits == 1
    row = db.added[0]
    assert isinstance(row, LlmUsageLog)
    assert row.user_id == USER_ID
    assert row.op == "generate_structured"
    assert row.model == "gpt-5"
    assert row.input_tokens == 11
    assert row.output_tokens == 22
    assert row.total_tokens == 33


@pytest.mark.asyncio
async def test_record_llm_usage_noop_when_usage_none():
    # Arrange
    db = _FakeSession()

    # Act
    await record_llm_usage(db, user_id=USER_ID, usage=None)

    # Assert: usage が無ければ insert も commit もしない
    assert db.added == []
    assert db.commits == 0


@pytest.mark.asyncio
async def test_record_llm_usage_allows_null_token_fields():
    # Arrange: token フィールドが欠けても（None）壊れず NULL 許容で保存する
    db = _FakeSession()
    usage = LlmUsage(
        op="generate_image",
        model="gpt-image-1",
        input_tokens=None,
        output_tokens=None,
        total_tokens=None,
    )

    # Act
    await record_llm_usage(db, user_id=USER_ID, usage=usage)

    # Assert
    assert len(db.added) == 1
    assert db.commits == 1
    row = db.added[0]
    assert row.input_tokens is None
    assert row.output_tokens is None
    assert row.total_tokens is None
