import uuid
from types import SimpleNamespace

import pytest

from app.domain.outfits.orchestration import DEFAULT_BATCH_TPO
from jobs import generate_outfits_for_all_users as job


def test_build_parser_defaults_to_business() -> None:
    args = job.build_parser().parse_args([])

    assert args.tpo == DEFAULT_BATCH_TPO
    assert args.page_size == job.DEFAULT_PAGE_SIZE


@pytest.mark.asyncio
async def test_run_job_processes_all_users_and_continues_on_failure(
    monkeypatch,
) -> None:
    user_a = job.UserBatchTarget(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        default_region_code="13_01",
    )
    user_b = job.UserBatchTarget(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        default_region_code=None,
    )
    user_c = job.UserBatchTarget(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        default_region_code="27_01",
    )

    async def fake_fetch_user_batch(*, limit: int, offset: int):
        assert limit == 2
        pages = {
            0: [user_a, user_b],
            2: [user_c],
            3: [],
        }
        return pages[offset]

    processed: list[tuple[uuid.UUID, str]] = []

    async def fake_process_user(*, user: job.UserBatchTarget, tpo: str):
        processed.append((user.id, tpo))
        if user.id == user_b.id:
            raise RuntimeError("boom")
        return SimpleNamespace(
            id=user.id,
            coordinate_image_url=None
            if user.id == user_c.id
            else "https://example.com",
        )

    monkeypatch.setattr(job, "fetch_user_batch", fake_fetch_user_batch)
    monkeypatch.setattr(job, "process_user", fake_process_user)

    stats = await job.run_job(tpo="business", page_size=2)

    assert processed == [
        (user_a.id, "business"),
        (user_b.id, "business"),
        (user_c.id, "business"),
    ]
    assert stats.processed == 3
    assert stats.succeeded == 2
    assert stats.failed == 1
    assert stats.image_skipped == 1
    assert stats.image_generated == 1


def test_should_fail_job_only_when_no_images_were_generated() -> None:
    assert not job.should_fail_job(
        job.BatchJobStats(
            processed=3,
            succeeded=2,
            failed=1,
            image_skipped=1,
        )
    )
    assert job.should_fail_job(
        job.BatchJobStats(
            processed=3,
            succeeded=2,
            failed=1,
            image_skipped=2,
        )
    )
