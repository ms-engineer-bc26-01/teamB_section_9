from scripts.check_api_contract import compute_drift


def test_undocumented_route_fails() -> None:
    code, msgs = compute_drift(spec_paths={}, app_paths={"/api/v1/items": {"get"}})
    assert code == 1
    assert any("[FAIL]" in m for m in msgs)


def test_unimplemented_spec_warns() -> None:
    code, msgs = compute_drift(spec_paths={"/api/v1/items": {"get"}}, app_paths={})
    assert code == 0
    assert any("[WARN]" in m for m in msgs)


def test_matching_routes_pass() -> None:
    code, msgs = compute_drift(
        spec_paths={"/api/v1/items": {"get"}},
        app_paths={"/api/v1/items": {"get"}},
    )
    assert code == 0
    assert not any("[FAIL]" in m for m in msgs)


def test_undocumented_method_fails() -> None:
    code, msgs = compute_drift(
        spec_paths={"/api/v1/items": {"get"}},
        app_paths={"/api/v1/items": {"get", "post"}},
    )
    assert code == 1
    assert any("Undocumented method" in m for m in msgs)
