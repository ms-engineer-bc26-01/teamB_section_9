from fastapi.testclient import TestClient

from app.api.v1.schemas.regions import to_region_schema
from app.constants.regions import (
    REGIONS,
    get_region_coordinates,
    get_regions_by_prefecture,
)


def test_list_regions_returns_all_regions(client: TestClient) -> None:
    response = client.get("/api/v1/regions")

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == len(REGIONS)

    first_item = body["items"][0]
    assert set(first_item) == {
        "code",
        "prefecture_code",
        "prefecture_name",
        "name",
        "city",
        "latitude",
        "longitude",
    }


def test_list_regions_filters_by_prefecture_code(client: TestClient) -> None:
    response = client.get("/api/v1/regions", params={"prefecture_code": "13"})

    assert response.status_code == 200
    body = response.json()
    expected_regions = get_regions_by_prefecture("13")
    assert len(body["items"]) == len(expected_regions)
    assert {item["code"] for item in body["items"]} == set(expected_regions)
    assert all(item["prefecture_code"] == "13" for item in body["items"])


def test_list_regions_rejects_invalid_prefecture_code(client: TestClient) -> None:
    response = client.get("/api/v1/regions", params={"prefecture_code": "abc"})

    assert response.status_code == 422


def test_get_region_coordinates_returns_lat_lng() -> None:
    assert get_region_coordinates("13_01") == (35.6895, 139.6917)


def test_get_region_coordinates_returns_none_for_unknown_code() -> None:
    assert get_region_coordinates("99_99") is None


def test_to_region_schema_resolves_known_code() -> None:
    region = to_region_schema("13_01")
    assert region is not None
    assert region.code == "13_01"
    assert region.prefecture_code == "13"
    assert region.prefecture_name == "東京都"
    assert (region.latitude, region.longitude) == (35.6895, 139.6917)


def test_to_region_schema_returns_none_for_unknown_code() -> None:
    assert to_region_schema("99_99") is None
