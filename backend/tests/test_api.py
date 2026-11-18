"""Test can CSDL dang chay va da nap du lieu thu (xem README)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_health_db_reports_postgis():
    res = client.get("/health/db")
    assert res.status_code == 200
    assert res.json()["postgis"].startswith("3.")


def test_kpis_have_unit_and_description():
    kpis = client.get("/api/v1/kpis").json()
    assert {k["code"] for k in kpis} >= {"latency_ms", "packet_loss_pct"}
    assert all(k["unit"] and k["description"] for k in kpis)


def test_regions_is_geojson_without_station_fields():
    body = client.get("/api/v1/regions").json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 9
    props = body["features"][0]["properties"]
    assert set(props) == {"region_code", "name", "level"}
    assert body["features"][0]["geometry"]["type"] == "MultiPolygon"
