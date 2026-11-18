"""Test API KPI tren du lieu thu (scripts/make_sample_data.py).

Du lieu thu co 2 o co y de trong:
  R-1-1 / latency_ms / 2026-10-01 va R-2-2 / packet_loss_pct / 2026-09-01
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SEP, OCT = "2026-09-01", "2026-10-01"


def by_region(items):
    return {i["region_code"]: i for i in items}


def test_kpi_values_returns_all_regions_with_unit():
    body = client.get("/api/v1/kpi-values", params={"kpi": "latency_ms", "period_start": OCT}).json()
    assert body["kpi"]["unit"] == "ms"
    assert len(body["items"]) == 9


def test_missing_is_null_not_zero():
    items = by_region(client.get(
        "/api/v1/kpi-values", params={"kpi": "latency_ms", "period_start": OCT}
    ).json()["items"])
    assert items["R-1-1"] == {**items["R-1-1"], "value": None, "status": "missing"}
    assert items["R-0-0"]["status"] == "ok" and items["R-0-0"]["value"] is not None


def test_period_without_any_data_is_missing_everywhere():
    items = client.get(
        "/api/v1/kpi-values", params={"kpi": "latency_ms", "period_start": "2020-01-01"}
    ).json()["items"]
    assert all(i["value"] is None and i["status"] == "missing" for i in items)


def test_region_filter():
    res = client.get("/api/v1/kpi-values",
                     params={"kpi": "latency_ms", "period_start": OCT, "region": ["R-0-0", "R-2-2"]})
    assert [i["region_code"] for i in res.json()["items"]] == ["R-0-0", "R-2-2"]


def test_unknown_kpi_is_404():
    res = client.get("/api/v1/kpi-values", params={"kpi": "khong_co", "period_start": OCT})
    assert res.status_code == 404


def test_bad_date_and_period_type_are_422():
    assert client.get("/api/v1/kpi-values",
                      params={"kpi": "latency_ms", "period_start": "10/2026"}).status_code == 422
    assert client.get("/api/v1/kpi-values", params={
        "kpi": "latency_ms", "period_start": OCT, "period_type": "year"}).status_code == 422


def test_region_detail_series():
    body = client.get("/api/v1/regions/R-1-1/kpis").json()
    lat = next(k for k in body["kpis"] if k["code"] == "latency_ms")
    assert [p["period_start"] for p in lat["series"]] == [SEP, OCT]
    assert lat["series"][1]["value"] is None and lat["series"][1]["status"] == "missing"


def test_region_detail_date_range_and_kpi_filter():
    body = client.get("/api/v1/regions/R-0-0/kpis",
                      params={"kpi": "latency_ms", "from": OCT, "to": OCT}).json()
    assert len(body["kpis"]) == 1 and len(body["kpis"][0]["series"]) == 1


def test_region_detail_errors():
    assert client.get("/api/v1/regions/KHONG-CO/kpis").status_code == 404
    assert client.get("/api/v1/regions/R-0-0/kpis",
                      params={"from": OCT, "to": SEP}).status_code == 422


def test_compare_delta_is_b_minus_a():
    items = by_region(client.get("/api/v1/compare", params={
        "kpi": "latency_ms", "period_a": SEP, "period_b": OCT}).json()["items"])
    r = items["R-0-0"]
    assert r["delta"] == round(r["value_b"] - r["value_a"], 4)


def test_compare_delta_null_when_one_period_missing():
    items = by_region(client.get("/api/v1/compare", params={
        "kpi": "latency_ms", "period_a": SEP, "period_b": OCT}).json()["items"])
    assert items["R-1-1"]["status_b"] == "missing" and items["R-1-1"]["delta"] is None
