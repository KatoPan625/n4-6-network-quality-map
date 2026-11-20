"""Test API KPI tren du lieu thu BE-SAMPLE (scripts/load_sample.py, cac ca co y o CASE_HOUR)."""

from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import engine, get_session
from app.main import app
from scripts.load_sample import (
    CASE_HOUR,
    INVALID_CELL,
    MISSING_PROVINCE,
    PARTIAL_WARD,
    POOR_WARD,
    ZERO_TRAFFIC_WARD,
)

client = TestClient(app)
HOUR = CASE_HOUR.strftime("%Y-%m-%dT%H:%M")  # gio VN, khong kem mui gio
DAY = CASE_HOUR.date().isoformat()
SRC = {"source": "BE-SAMPLE"}


def get(path, **params):
    return client.get(path, params={**SRC, **params})


def values(**params) -> dict:
    return {i["region_code"]: i for i in get("/api/v1/kpi-values", **params).json()["items"]}


def test_hour_ward_level_returns_all_168_wards_with_source_label():
    body = get("/api/v1/kpi-values", kpi="cssr", level="ward", at=HOUR).json()
    assert len(body["items"]) == 168
    assert body["source"]["source_code"] == "BE-SAMPLE"
    assert body["source"]["data_nature"] == "simulated"
    assert body["period"] == {"type": "hour", "at": CASE_HOUR.isoformat()}
    assert body["kpi"]["unit"] == "%"


def test_partial_ward_keeps_value_and_reports_cells():
    item = values(kpi="cssr", level="ward", at=HOUR)[PARTIAL_WARD]
    assert item["status"] == "partial"
    assert item["value"] is not None
    assert (item["cells_reported"], item["cells_total"]) == (1, 2)


def test_zero_traffic_ward_has_null_value_and_reason():
    item = values(kpi="cssr", level="ward", at=HOUR)[ZERO_TRAFFIC_WARD]
    assert item["value"] is None
    assert item["status"] == "ok"
    assert item["reason"] == "no_positive_traffic"
    assert "aggregation_status" not in item


def test_invalid_cell_makes_ward_partial():
    ward = INVALID_CELL.split("-")[1]
    item = values(kpi="user_throughput", level="ward", at=HOUR)[ward]
    assert item["status"] == "partial" and item["cells_reported"] == 1


def test_missing_province_is_null_not_zero():
    item = values(kpi="traffic", at=HOUR)[MISSING_PROVINCE]
    assert item["value"] is None
    assert item["status"] == "missing"
    assert item["cells_reported"] == 0 and item["cells_total"] == 20


def test_province_level_returns_34_and_traffic_is_sum():
    items = values(kpi="traffic", at=HOUR)
    assert len(items) == 34
    wards = values(kpi="traffic", level="ward", at=HOUR)
    total = sum(w["value"] for w in wards.values() if w["value"] is not None)
    assert abs(items["79"]["value"] - total) < 1e-3


def test_poor_ward_is_lower_than_city():
    ward = values(kpi="cssr", level="ward", period_type="day", at=DAY)[POOR_WARD]["value"]
    city = values(kpi="cssr", period_type="day", at=DAY)["79"]["value"]
    assert ward < city - 3


def test_day_status_uses_cell_hours():
    item = values(kpi="traffic", period_type="day", at=DAY)[MISSING_PROVINCE]
    assert item["status"] == "partial"
    assert (item["cell_hours_reported"], item["cell_hours_expected"]) == (460, 480)


def test_hour_accepts_offset_utc_and_plus_decoded_as_space():
    naive = values(kpi="cssr", at=HOUR)["79"]["value"]
    utc = (CASE_HOUR - timedelta(hours=7)).strftime("%Y-%m-%dT%H:%MZ")
    assert values(kpi="cssr", at=utc)["79"]["value"] == naive
    assert values(kpi="cssr", at=f"{HOUR} 07:00")["79"]["value"] == naive


def test_region_filter():
    items = get("/api/v1/kpi-values", kpi="cssr", level="ward", at=HOUR, region=[POOR_WARD])
    assert [i["region_code"] for i in items.json()["items"]] == [POOR_WARD]


def test_default_source_is_sim_4g():
    res = client.get("/api/v1/kpi-values", params={"kpi": "cssr", "at": HOUR})
    assert res.json()["source"]["source_code"] == "SIM-4G-2026-10"


def test_not_found_is_404():
    assert get("/api/v1/kpi-values", kpi="khong_co", at=HOUR).status_code == 404
    assert get("/api/v1/kpi-values", kpi="cssr", at=HOUR, source="KHONG-CO").status_code == 404
    assert get("/api/v1/regions/KHONG-CO/kpis").status_code == 404


def test_bad_time_or_params_are_422():
    for params in (
        {"at": "10/2026"},
        {"at": HOUR.replace(":00", ":30")},
        {"at": "2026-10-20T08:00"},  # ngoai khoang 72 gio cua BE-SAMPLE
        {"at": DAY, "period_type": "week"},
        {"at": HOUR, "level": "district"},
    ):
        assert get("/api/v1/kpi-values", kpi="cssr", **params).status_code == 422, params


def test_region_series_daily_by_default_in_kpi_order():
    body = get(f"/api/v1/regions/{POOR_WARD}/kpis").json()
    assert (body["region_level"], body["parent_code"]) == ("ward", "79")
    assert [k["kpi_code"] for k in body["kpis"]] == [
        "cssr",
        "service_drop_all",
        "user_throughput",
        "traffic",
    ]
    assert [p["at"] for p in body["kpis"][0]["series"]] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
    ]


def test_region_series_hour_range_and_errors():
    hour_a = (CASE_HOUR - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
    body = get(
        f"/api/v1/regions/{ZERO_TRAFFIC_WARD}/kpis",
        kpi="cssr",
        period_type="hour",
        **{"from": hour_a, "to": HOUR},
    ).json()
    series = body["kpis"][0]["series"]
    assert len(series) == 2 and series[1]["reason"] == "no_positive_traffic"
    bad = get(f"/api/v1/regions/{POOR_WARD}/kpis", **{"from": "2026-10-03", "to": "2026-10-01"})
    assert bad.status_code == 422


def test_compare_delta_is_b_minus_a_and_null_when_missing():
    hour_a = (CASE_HOUR - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
    items = {
        i["region_code"]: i
        for i in get(
            "/api/v1/compare", kpi="cssr", level="ward", period_type="hour", a=hour_a, b=HOUR
        ).json()["items"]
    }
    ok = items[POOR_WARD]
    assert ok["delta"] == round(ok["value_b"] - ok["value_a"], 4)
    assert items[ZERO_TRAFFIC_WARD]["value_b"] is None
    assert items[ZERO_TRAFFIC_WARD]["delta"] is None


THRESHOLDS_SQL = Path(__file__).resolve().parents[2] / "db" / "N4.6_KPI_Thresholds.sql"


def load_thresholds(conn):
    # goi thang psycopg: SQLAlchemy doc '%' trong file la placeholder
    conn.connection.driver_connection.execute(THRESHOLDS_SQL.read_text(encoding="utf-8"))


def test_quality_level_also_for_partial_regions():
    """Nap file nguong de xuat, refresh MV trong 1 giao dich roi rollback, khong de lai gi."""
    with engine.connect() as conn:
        trans = conn.begin()
        load_thresholds(conn)
        checks = dict(
            conn.execute(text("SELECT kpi_code, check_result FROM v_kpi_threshold_check")).all()
        )
        conn.execute(text("REFRESH MATERIALIZED VIEW mv_region_kpi"))
        app.dependency_overrides[get_session] = lambda: Session(bind=conn)
        try:
            items = values(kpi="cssr", level="ward", at=HOUR)
        finally:
            app.dependency_overrides.clear()
            trans.rollback()
    assert checks == dict.fromkeys(["cssr", "service_drop_all", "user_throughput"], "ok")
    partial = items[PARTIAL_WARD]
    assert partial["status"] == "partial" and partial["quality_level"] is not None
    assert items[POOR_WARD]["quality_level"] == "poor"
    assert items[ZERO_TRAFFIC_WARD]["quality_level"] is None
    for i in items.values():
        if i["value"] is not None:
            v = i["value"]
            assert i["quality_level"] == ("good" if v >= 98 else "medium" if v >= 95 else "poor")
            assert i["threshold_type"] == "team_proposed"


def test_drop_rate_boundary_is_inclusive_upper():
    """service_drop_all cang thap cang tot: dung 2 -> good, dung 5 -> medium (QCVN ghi <=)."""
    special = {PARTIAL_WARD, POOR_WARD, ZERO_TRAFFIC_WARD, INVALID_CELL.split("-")[1]}
    before = values(kpi="service_drop_all", level="ward", at=HOUR)
    w2, w5 = [c for c, i in before.items() if i["status"] == "ok" and c not in special][:2]
    with engine.connect() as conn:
        trans = conn.begin()
        load_thresholds(conn)
        for ward, v in ((w2, 2), (w5, 5)):
            conn.execute(
                text(
                    "UPDATE cell_kpi_values x SET value = :v FROM cells c, regions r, kpis k, "
                    "data_sources s WHERE x.cell_id = c.cell_id AND c.ward_id = r.region_id "
                    "AND x.kpi_id = k.kpi_id AND x.source_id = s.source_id "
                    "AND r.region_code = :w AND k.kpi_code = 'service_drop_all' "
                    "AND s.source_code = 'BE-SAMPLE' AND x.period_start = :t AND x.status = 'ok'"
                ),
                {"v": v, "w": ward, "t": CASE_HOUR},
            )
        conn.execute(text("REFRESH MATERIALIZED VIEW mv_region_kpi"))
        app.dependency_overrides[get_session] = lambda: Session(bind=conn)
        try:
            items = values(kpi="service_drop_all", level="ward", at=HOUR)
        finally:
            app.dependency_overrides.clear()
            trans.rollback()
    assert (items[w2]["value"], items[w2]["quality_level"]) == (2, "good")
    assert (items[w5]["value"], items[w5]["quality_level"]) == (5, "medium")
    for i in items.values():
        if i["value"] is not None:
            v = i["value"]
            assert i["quality_level"] == ("good" if v <= 2 else "medium" if v <= 5 else "poor")
