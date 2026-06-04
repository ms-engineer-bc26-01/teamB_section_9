from scripts.seed_bypass_clothes import BYPASS_USER_ID, SEED_CLOTHES


def test_seed_bypass_clothes_has_expected_volume_and_unique_ids() -> None:
    assert BYPASS_USER_ID.hex == "00000000000000000000000000000001"
    assert len(SEED_CLOTHES) == 20
    assert len({item.id for item in SEED_CLOTHES}) == len(SEED_CLOTHES)


def test_seed_bypass_clothes_covers_diverse_coordination_cases() -> None:
    categories = {item.category for item in SEED_CLOTHES}
    tpo_tags = {tag for item in SEED_CLOTHES for tag in item.tpo_tags}
    seasons = {season for item in SEED_CLOTHES for season in item.season}

    assert {"tops", "bottoms", "outer", "shoes"}.issubset(categories)
    assert {"casual", "business", "date", "outdoor", "rainy"}.issubset(tpo_tags)
    assert {"spring", "summer", "autumn", "winter"}.issubset(seasons)


def test_seed_bypass_clothes_contains_prompt_friendly_metadata() -> None:
    assert all(item.name for item in SEED_CLOTHES)
    assert all(item.category for item in SEED_CLOTHES)
    assert all(item.season for item in SEED_CLOTHES)
    assert all(item.tpo_tags for item in SEED_CLOTHES)
    assert any(item.memo for item in SEED_CLOTHES)
    assert any(item.is_favorite for item in SEED_CLOTHES)
