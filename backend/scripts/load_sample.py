"""Sinh va nap du lieu THU cua Backend (nguon BE-SAMPLE) vao CSDL, roi refresh 2 materialized view.

Khong phai bo mo phong chinh thuc (SIM-4G-2026-10, phan cua Vu); BE-SAMPLE co is_default = FALSE.
Cell: 2 cell/phuong TP.HCM (336) + 20 cell/tinh con lai (660) = 996 cell 4G, khong co toa do.
Thoi gian: 72 gio tu 01/10/2026 00:00 +07. Gia tri co quy luat gio cao diem va mot phuong "co van de".
Cac ca co y de test (tests/test_kpi_api.py) nam o CASE_HOUR, xem hang so ben duoi.
Can chay scripts/load_regions.py truoc. Chay lai nhieu lan khong trung (upsert).
Chay: uv run python scripts/load_sample.py
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings

VN = ZoneInfo("Asia/Ho_Chi_Minh")
SOURCE = "BE-SAMPLE"
START = datetime(2026, 10, 1, tzinfo=VN)
HOURS = 72
HCM = "79"
KPIS = ("cssr", "service_drop_all", "user_throughput", "traffic")

CASE_HOUR = START + timedelta(hours=44)  # 2026-10-02 20:00 +07, gio cao diem
PARTIAL_WARD = "25747"  # cell -1 mat cssr -> phuong partial cho cssr
ZERO_TRAFFIC_WARD = "25750"  # ca 2 cell traffic = 0 -> cssr no_positive_traffic
INVALID_CELL = "HCM-25760-1"  # user_throughput invalid (co quality_note)
MISSING_PROVINCE = "01"  # moi cell, moi KPI missing -> tinh missing
POOR_WARD = "25760"  # phuong "co van de" suot 72 gio: cssr thap, rot cao

SOURCE_SQL = """
INSERT INTO n46.data_sources (source_code, source_name, source_type, data_nature, description,
    spatial_scope, period_from, period_to, collection_method, method_version, random_seed,
    assumptions, limitations, is_default)
VALUES (%(code)s, 'Du lieu thu cua Backend', 'simulation', 'simulated',
    'Du lieu thu de test API; khong dung cho bao cao.',
    '34 tinh/thanh; 168 phuong/xa TP.HCM; 996 cell 4G.', %(start)s, %(end)s,
    'scripts/load_sample.py: random co seed, he so tai theo gio, mot phuong co van de.',
    'be-sample', 46, 'Tai cao 19-22h lam giam throughput va cssr; khong co co so do thuc te.',
    'Chi de test Backend; khong phai so lieu VNPT.', FALSE)
ON CONFLICT (source_code) DO NOTHING
"""
CELL_SQL = """
INSERT INTO n46.cells (cell_code, province_id, ward_id)
SELECT %s, p.region_id, w.region_id FROM n46.regions p LEFT JOIN n46.regions w ON w.region_code = %s
WHERE p.region_code = %s
ON CONFLICT (cell_code) DO NOTHING
"""
VALUE_SQL = """
INSERT INTO n46.cell_kpi_values (source_id, cell_id, kpi_id, period_start, value, status, quality_note)
SELECT s.source_id, c.cell_id, k.kpi_id, t.period_start, t.value, t.status, t.quality_note
FROM tmp_values t
JOIN n46.cells c ON c.cell_code = t.cell_code
JOIN n46.kpis k ON k.kpi_code = t.kpi_code
JOIN n46.data_sources s ON s.source_code = %s
ON CONFLICT (source_id, cell_id, kpi_id, period_start) DO UPDATE SET
    value = EXCLUDED.value, status = EXCLUDED.status, quality_note = EXCLUDED.quality_note
"""


def make_cells(regions: list[tuple[str, str, str | None]]) -> list[tuple[str, str, str | None]]:
    """regions: (code, level, parent_code). Tra ve (cell_code, province_code, ward_code)."""
    cells = []
    for code, level, parent in sorted(regions):
        if level == "ward":
            cells += [(f"HCM-{code}-{n}", parent, code) for n in (1, 2)]
        elif code != HCM:
            cells += [(f"P{code}-{n:02d}", code, None) for n in range(1, 21)]
    return cells


def load_factor(hour: int) -> float:
    if 1 <= hour <= 5:
        return 0.2
    if 19 <= hour <= 22:
        return 1.0
    return 0.6


def make_rows(cells: list[tuple[str, str, str | None]]) -> list[tuple]:
    """Moi dong: (cell_code, kpi_code, period_start, value, status, quality_note)."""
    rng = random.Random(46)
    rows = []
    for h in range(HOURS):
        ts = START + timedelta(hours=h)
        load = load_factor(ts.hour)
        for cell, prov, ward in cells:
            urban = 1.0 if prov == HCM else 0.6
            poor = ward == POOR_WARD
            vals = {
                "cssr": 99.6 - 1.2 * load - rng.uniform(0, 0.6) - (5 if poor else 0),
                "service_drop_all": 0.3 + 0.8 * load + rng.uniform(0, 0.3) + (2 if poor else 0),
                "user_throughput": max(1.0, 55 - 25 * load + rng.uniform(-5, 5)),
                "traffic": urban * load * rng.uniform(1.5, 3.0),
            }
            for kpi in KPIS:
                value, status, note = round(vals[kpi], 4), "ok", None
                at_case = ts == CASE_HOUR
                # thieu ngau nhien 0,05%, tru gio test de cac ca co dinh khong bi lech
                random_gap = rng.random() < 0.0005 and not at_case
                if (at_case and prov == MISSING_PROVINCE) or random_gap:
                    value, status = None, "missing"
                if at_case and kpi == "cssr" and cell == f"HCM-{PARTIAL_WARD}-1":
                    value, status = None, "missing"
                if at_case and kpi == "traffic" and ward == ZERO_TRAFFIC_WARD:
                    value, status = 0.0, "ok"
                if at_case and kpi == "user_throughput" and cell == INVALID_CELL:
                    value, status, note = None, "invalid", "Mau loi gia lap (du lieu thu)"
                rows.append((cell, kpi, ts, value, status, note))
    return rows


def main() -> None:
    dsn = settings.database_url.replace("postgresql+psycopg", "postgresql")
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT r.region_code, r.region_level, p.region_code FROM n46.regions r "
            "LEFT JOIN n46.regions p ON p.region_id = r.parent_region_id"
        )
        cells = make_cells(cur.fetchall())
        if not cells:
            sys.exit("Loi: chua co regions, chay scripts/load_regions.py truoc")
        cur.execute(
            SOURCE_SQL, {"code": SOURCE, "start": START, "end": START + timedelta(hours=HOURS)}
        )
        cur.executemany(CELL_SQL, [(c, w, p) for c, p, w in cells])
        rows = make_rows(cells)
        cur.execute(
            "CREATE TEMP TABLE tmp_values (cell_code text, kpi_code text, period_start timestamptz,"
            " value numeric, status text, quality_note text) ON COMMIT DROP"
        )
        with cur.copy("COPY tmp_values FROM STDIN") as copy:
            for r in rows:
                copy.write_row(r)
        cur.execute(VALUE_SQL, (SOURCE,))
        cur.execute(
            "SELECT count(*) FROM n46.cell_kpi_values v JOIN n46.data_sources s USING (source_id) "
            "WHERE s.source_code = %s",
            (SOURCE,),
        )
        loaded = cur.fetchone()[0]
    if loaded != len(rows):
        sys.exit(f"Loi: sinh {len(rows)} dong nhung CSDL co {loaded} dong cua {SOURCE}")
    refresh(dsn)
    print(f"Da nap {len(cells)} cell, {loaded} gia tri KPI cho {SOURCE}; da refresh MV")


def refresh(dsn: str) -> None:
    sql = Path(__file__).resolve().parents[2] / "db" / "N4.6_Refresh_Materialized_Views.sql"
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
