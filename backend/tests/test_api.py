"""Test can CSDL dang chay voi schema cua du an va da nap scripts/load_regions.py (xem README)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_health_db_reports_postgis():
    res = client.get("/health/db")
    assert res.status_code == 200
    assert res.json()["postgis"].startswith("3.")


def test_kpis_are_the_4_mobile_kpis_in_order():
    kpis = client.get("/api/v1/kpis").json()
    assert [k["kpi_code"] for k in kpis] == [
        "cssr",
        "service_drop_all",
        "user_throughput",
        "traffic",
    ]
    by_code = {k["kpi_code"]: k for k in kpis}
    assert by_code["traffic"]["aggregation_rule"] == "sum"
    assert by_code["traffic"]["higher_is_better"] is None
    assert by_code["service_drop_all"]["higher_is_better"] is False
    assert all(k["calculation_method"] and k["unit"] for k in kpis)


def test_sources_list_default_first_with_local_period():
    sources = client.get("/api/v1/sources").json()
    assert sources[0]["is_default"] is True
    assert {s["source_code"] for s in sources} >= {"SIM-4G-2026-10", "BE-SAMPLE"}
    assert all(s["data_nature"] == "simulated" for s in sources)
    assert sources[0]["period_from"].endswith("+07:00")


def test_regions_province_geojson_without_station_fields():
    body = client.get("/api/v1/regions").json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 34
    f = next(f for f in body["features"] if f["id"] == "79")
    assert f["properties"] == {
        "region_code": "79",
        "region_name": "Thành phố Hồ Chí Minh",
        "region_level": "province",
        "parent_code": None,
    }
    assert f["geometry"]["type"] == "MultiPolygon"


def test_regions_ward_level_is_168_hcm_wards():
    features = client.get("/api/v1/regions", params={"level": "ward"}).json()["features"]
    assert len(features) == 168
    assert {f["properties"]["parent_code"] for f in features} == {"79"}


def test_regions_geojson_is_gzipped_when_client_accepts():
    res = client.get("/api/v1/regions", headers={"Accept-Encoding": "gzip"})
    assert res.headers["content-encoding"] == "gzip"
    assert res.json()["type"] == "FeatureCollection"
    plain = client.get("/api/v1/regions", headers={"Accept-Encoding": "identity"})
    assert "content-encoding" not in plain.headers


def test_regions_bad_level_is_422():
    assert client.get("/api/v1/regions", params={"level": "district"}).status_code == 422
