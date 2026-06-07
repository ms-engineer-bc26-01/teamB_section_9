from scripts.seed_bypass_user import (
    BYPASS_USER_EMAIL,
    BYPASS_USER_ID,
    DEFAULT_REGION_CODE,
)


def test_seed_bypass_user_constants_match_bypass_auth_user() -> None:
    assert BYPASS_USER_ID.hex == "00000000000000000000000000000001"
    assert BYPASS_USER_EMAIL == "test@example.com"
    assert DEFAULT_REGION_CODE == "13_01"
