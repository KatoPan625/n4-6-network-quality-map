"""Test can CSDL dang chay voi schema V2.1 (xem README)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_health_db_reports_postgis():
    res = client.get("/health/db")
    assert res.status_code == 200
    assert res.json()["postgis"].startswith("3.")


def test_kpis_are_the_8_fixed_network_kpis_in_order():
    kpis = client.get("/api/v1/kpis").json()
    assert [k["kpi_code"] for k in kpis] == [
        "download_throughput",
        "upload_throughput",
        "latency",
        "jitter",
        "packet_loss_rate",
        "network_availability",
        "http_ip_access_failure_ratio",
        "http_dropped_sessions_ratio",
    ]
    assert all(k["unit"] in {"Mbps", "ms", "%"} and k["description"] for k in kpis)
    assert all(k["is_ratio"] == (k["unit"] == "%") for k in kpis)


def test_regions_is_165_cell_geojson_without_station_fields():
    body = client.get("/api/v1/regions").json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 165
    f = body["features"][0]
    assert f["id"] == "G1K-683-1190"
    assert set(f["properties"]) == {"region_code", "region_name", "region_level"}
    assert f["properties"]["region_level"] == "grid_1km"
    assert f["geometry"]["type"] == "MultiPolygon"
