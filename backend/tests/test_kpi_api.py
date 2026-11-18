"""Test API KPI tren du lieu thu BE-SAMPLE (scripts/make_sample_data.py).

Du lieu thu co y de:
  G1K-690-1195 / latency / W2 : co dong, status missing
  G1K-683-1190 / latency / W2 : khong co dong nao
  G1K-697-1200 / packet_loss_rate / W1 : status invalid
"""

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import engine, get_session
from app.main import app

client = TestClient(app)
W1, W2 = "2026-10-19", "2026-10-26"
SRC = {"source": "BE-SAMPLE"}


def get(path, **params):
    return client.get(path, params={**SRC, **params})


def by_region(items):
    return {i["region_code"]: i for i in items}


def test_kpi_values_returns_all_cells_with_unit_and_source_label():
    body = get("/api/v1/kpi-values", kpi="latency", period_start=W2).json()
    assert body["kpi"] == {"kpi_code": "latency", "unit": "ms", "higher_is_better": False}
    assert body["source"]["source_code"] == "BE-SAMPLE"
    assert body["source"]["data_nature"] == "simulated"
    assert body["period"] == {"type": "week", "start": W2}
    assert len(body["items"]) == 165


def test_default_source_is_sim_v1():
    body = client.get("/api/v1/kpi-values", params={"kpi": "latency", "period_start": W2}).json()
    assert body["source"]["source_code"] == "SIM-V1"
    assert body["source"]["data_nature"] == "simulated"


def test_unknown_source_is_404():
    res = client.get(
        "/api/v1/kpi-values", params={"kpi": "latency", "period_start": W2, "source": "KHONG-CO"}
    )
    assert res.status_code == 404


def test_missing_is_null_not_zero():
    items = by_region(get("/api/v1/kpi-values", kpi="latency", period_start=W2).json()["items"])
    for code in ("G1K-690-1195", "G1K-683-1190"):  # co dong missing / khong co dong
        assert items[code]["value"] is None and items[code]["status"] == "missing"
        assert items[code]["quality_level"] is None
    ok = items["G1K-684-1190"]
    assert ok["status"] == "ok" and ok["value"] is not None and ok["sample_count"] > 0


def test_invalid_is_null():
    items = by_region(
        get("/api/v1/kpi-values", kpi="packet_loss_rate", period_start=W1).json()["items"]
    )
    assert items["G1K-697-1200"]["value"] is None
    assert items["G1K-697-1200"]["status"] == "invalid"


def test_quality_level_null_without_thresholds():
    items = get("/api/v1/kpi-values", kpi="latency", period_start=W1).json()["items"]
    assert all(i["quality_level"] is None for i in items)


def test_quality_level_from_thresholds():
    """Them nguong tam trong 1 giao dich roi rollback, khong de lai gi trong CSDL."""
    with engine.connect() as conn:
        trans = conn.begin()
        conn.execute(
            text(
                "INSERT INTO kpi_thresholds (kpi_id, quality_level, min_value, max_value, "
                "threshold_type, threshold_basis) "
                "SELECT kpi_id, lv, lo, hi, 'team_proposed', 'chi de test' FROM kpis, "
                "(VALUES ('good', NULL::numeric, 20::numeric), ('medium', 20, 40), "
                "('poor', 40, NULL)) AS t(lv, lo, hi) WHERE kpi_code = 'latency'"
            )
        )
        app.dependency_overrides[get_session] = lambda: Session(bind=conn)
        try:
            items = get("/api/v1/kpi-values", kpi="latency", period_start=W1).json()["items"]
        finally:
            app.dependency_overrides.clear()
            trans.rollback()
    for i in items:
        expected = "good" if i["value"] < 20 else "medium" if i["value"] < 40 else "poor"
        assert i["quality_level"] == expected
        assert i["threshold_type"] == "team_proposed"


def test_region_filter():
    res = get(
        "/api/v1/kpi-values",
        kpi="latency",
        period_start=W2,
        region=["G1K-683-1190", "G1K-697-1200"],
    )
    assert [i["region_code"] for i in res.json()["items"]] == ["G1K-683-1190", "G1K-697-1200"]


def test_unknown_kpi_is_404():
    assert get("/api/v1/kpi-values", kpi="khong_co", period_start=W2).status_code == 404


def test_bad_date_period_type_and_non_monday_are_422():
    assert get("/api/v1/kpi-values", kpi="latency", period_start="10/2026").status_code == 422
    assert (
        get("/api/v1/kpi-values", kpi="latency", period_start=W2, period_type="month").status_code
        == 422
    )
    assert get("/api/v1/kpi-values", kpi="latency", period_start="2026-10-20").status_code == 422


def test_region_detail_series():
    body = get("/api/v1/regions/G1K-690-1195/kpis").json()
    assert body["source"]["source_code"] == "BE-SAMPLE"
    assert [k["kpi_code"] for k in body["kpis"]][:2] == ["download_throughput", "upload_throughput"]
    lat = next(k for k in body["kpis"] if k["kpi_code"] == "latency")
    assert [p["period_start"] for p in lat["series"]] == [W1, W2]
    assert lat["series"][1]["value"] is None and lat["series"][1]["status"] == "missing"


def test_region_detail_date_range_and_kpi_filter():
    body = get("/api/v1/regions/G1K-684-1190/kpis", kpi="latency", **{"from": W2, "to": W2}).json()
    assert len(body["kpis"]) == 1 and len(body["kpis"][0]["series"]) == 1


def test_region_detail_errors():
    assert get("/api/v1/regions/KHONG-CO/kpis").status_code == 404
    assert get("/api/v1/regions/G1K-684-1190/kpis", **{"from": W2, "to": W1}).status_code == 422


def test_compare_delta_is_b_minus_a():
    items = by_region(
        get("/api/v1/compare", kpi="latency", period_a=W1, period_b=W2).json()["items"]
    )
    r = items["G1K-684-1190"]
    assert r["delta"] == round(r["value_b"] - r["value_a"], 4)


def test_compare_delta_null_when_one_period_missing():
    items = by_region(
        get("/api/v1/compare", kpi="latency", period_a=W1, period_b=W2).json()["items"]
    )
    assert items["G1K-690-1195"]["status_b"] == "missing"
    assert items["G1K-690-1195"]["delta"] is None
