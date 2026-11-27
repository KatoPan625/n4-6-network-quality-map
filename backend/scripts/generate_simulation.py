"""Generate and load the official SIM-4G-2026-10 dataset.

Dataset is synthetic and intended for project demonstration, API testing,
aggregation validation, and QA. It does not represent measurements from
any real telecommunications operator.
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings

# ============================================================
# 1. DATASET CONFIGURATION
# ============================================================

VN = ZoneInfo("Asia/Ho_Chi_Minh")

SOURCE = "SIM-4G-2026-10"
START = datetime(2026, 10, 1, 0, 0, tzinfo=VN)
HOURS = 30 * 24
END = START + timedelta(hours=HOURS)

SEED = 202610
METHOD_VERSION = "sim-4g-v1.0"

HCM = "79"

KPIS = (
    "cssr",
    "service_drop_all",
    "user_throughput",
    "traffic",
)

EXPECTED_CELLS = 996
EXPECTED_ROWS = EXPECTED_CELLS * HOURS * len(KPIS)


# ============================================================
# 2. SIMULATION SCENARIOS
# ============================================================

# Khu vực mô phỏng chất lượng kém.
# Phường thứ hai sẽ được chọn tự động từ regions để bảo đảm tồn tại.
POOR_WARDS = {"25760"}

# Khu vực chịu ảnh hưởng bởi sự cố ngắn hạn.
INCIDENT_WARD = "25750"

# Thời gian xảy ra sự cố: 20:00–23:00 ngày 15/10/2026.
INCIDENT_START = datetime(2026, 10, 15, 20, 0, tzinfo=VN)
INCIDENT_END = datetime(2026, 10, 15, 23, 0, tzinfo=VN)

# Các tình huống QA cố định.
MISSING_PROVINCE = "01"
PARTIAL_WARD = "25747"
ZERO_TRAFFIC_WARD = "25750"
INVALID_CELL = "HCM-25760-1"

# Dùng để kiểm tra sự cố có ảnh hưởng đến chất lượng KPI.
INCIDENT_NOTE = "SIMULATED_INCIDENT_2026-10-15"


def validate_scenario_wards(
    regions: list[tuple[str, str, str | None]],
) -> set[str]:
    """Validate scenario ward codes and resolve the second poor ward.

    All configured scenario wards must exist in the database and belong
    to Ho Chi Minh City. The second poor ward is selected deterministically
    from existing HCM wards to avoid hard-coded nonexistent codes.
    """

    ward_parent = {code: parent for code, level, parent in regions if level == "ward"}

    configured_wards = POOR_WARDS | {
        INCIDENT_WARD,
        PARTIAL_WARD,
        ZERO_TRAFFIC_WARD,
    }

    missing_wards = configured_wards - set(ward_parent)

    if missing_wards:
        raise ValueError(f"Scenario ward codes not found in n46.regions: {sorted(missing_wards)}")

    invalid_parent = {code for code in configured_wards if ward_parent.get(code) != HCM}

    if invalid_parent:
        raise ValueError(f"Scenario ward codes do not belong to HCM: {sorted(invalid_parent)}")

    available_hcm_wards = sorted(
        code
        for code, parent in ward_parent.items()
        if parent == HCM and code not in configured_wards
    )

    if not available_hcm_wards:
        raise RuntimeError("Cannot find an additional HCM ward for the poor-quality scenario.")

    # Chọn mã đầu tiên theo thứ tự để kết quả ổn định.
    second_poor_ward = available_hcm_wards[0]

    poor_wards = POOR_WARDS | {second_poor_ward}

    print(f"Poor-quality wards: {sorted(poor_wards)}")
    print("Scenario ward validation: PASS")

    return poor_wards


# ============================================================
# 3. DATA SOURCE METADATA
# ============================================================

SOURCE_SQL = """
INSERT INTO n46.data_sources (
    source_code, source_name, source_type, data_nature, description,
    spatial_scope, period_from, period_to, timezone_name,
    collection_method, method_version, random_seed, assumptions, limitations
)
VALUES (
    %(code)s,
    'Du lieu mo phong mang 4G thang 10/2026',
    'simulation',
    'simulated',
    'Bo du lieu mo phong 4G phuc vu demo, kiem thu API va QA.',
    '34 tinh/thanh; 168 phuong/xa TP.HCM; 996 cell 4G.',
    %(start)s,
    %(end)s,
    'Asia/Ho_Chi_Minh',
    'Sinh du lieu bang Python random voi seed co dinh; mo hinh tai theo gio, khu vuc va su co.',
    %(version)s,
    %(seed)s,
    'Du lieu gia lap theo cac gia dinh ve gio cao diem, mat do khu vuc va cac muc chat luong KPI.',
    'Khong phai du lieu do dac thuc te; khong dai dien cho bat ky nha mang nao.'
)
ON CONFLICT (source_code) DO UPDATE SET
    source_name = EXCLUDED.source_name,
    source_type = EXCLUDED.source_type,
    data_nature = EXCLUDED.data_nature,
    description = EXCLUDED.description,
    spatial_scope = EXCLUDED.spatial_scope,
    period_from = EXCLUDED.period_from,
    period_to = EXCLUDED.period_to,
    timezone_name = EXCLUDED.timezone_name,
    collection_method = EXCLUDED.collection_method,
    method_version = EXCLUDED.method_version,
    random_seed = EXCLUDED.random_seed,
    assumptions = EXCLUDED.assumptions,
    limitations = EXCLUDED.limitations
"""


# ============================================================
# 4. CELL CONFIGURATION
# ============================================================

CELL_SQL = """
INSERT INTO n46.cells (cell_code, province_id, ward_id)
SELECT %s, p.region_id, w.region_id
FROM n46.regions p
LEFT JOIN n46.regions w ON w.region_code = %s
WHERE p.region_code = %s
ON CONFLICT (cell_code) DO NOTHING
"""


def make_cells(
    regions: list[tuple[str, str, str | None]],
) -> list[tuple[str, str, str | None]]:
    """Generate cell definitions from regions.

    Input:
        (region_code, region_level, parent_code)

    Output:
        (cell_code, province_code, ward_code)

    Rules:
        - 2 cells for every ward of HCM.
        - 20 cells for every other province.
    """

    cells = []

    for code, level, parent in sorted(regions):
        if level == "ward":
            if parent == HCM:
                cells.extend((f"HCM-{code}-{n}", parent, code) for n in (1, 2))

        elif code != HCM:
            cells.extend((f"P{code}-{n:02d}", code, None) for n in range(1, 21))

    return cells


# ============================================================
# 5. HOURLY LOAD FACTOR
# ============================================================


def load_factor(hour: int) -> float:
    """Network load factor by hour of day."""

    if 0 <= hour <= 5:
        return 0.25

    if 6 <= hour <= 8:
        return 0.65

    if 9 <= hour <= 16:
        return 0.55

    if 17 <= hour <= 18:
        return 0.85

    if 19 <= hour <= 22:
        return 1.0

    return 0.45


# ============================================================
# 6. CELL CHARACTERISTICS
# ============================================================


def get_cell_profile(
    cell: str,
    province: str,
    ward: str | None,
    poor_wards: set[str],
) -> str:
    """Classify a cell according to simulation scenarios."""

    if ward in poor_wards:
        return "poor"

    # Simulate some medium-quality cells in HCM.
    if cell.endswith("-2") and province == HCM:
        return "medium"

    return "good"


# ============================================================
# 7. KPI SIMULATION
# ============================================================


def simulate_kpis(
    rng: random.Random,
    hour: int,
    profile: str,
    province: str,
    ward: str | None,
) -> dict[str, float]:
    """Generate 4 KPIs for one cell at one hour.

    CSSR: successful call setup percentage.
    Service Drop: service drop rate (%).
    User Throughput: download speed (Mbps).
    Traffic: simulated traffic load.
    """

    load = load_factor(hour)

    # Area density effect.
    urban_factor = 1.0 if province == HCM else 0.75

    # Small variation between cells and hours.
    noise_cssr = rng.uniform(0.0, 0.5)
    noise_drop = rng.uniform(0.0, 0.3)
    noise_speed = rng.uniform(-2.0, 2.0)
    noise_traffic = rng.uniform(1.0, 3.0)

    # --------------------------------------------------------
    # 7.1. BASELINE
    # --------------------------------------------------------

    cssr = 99.5 - (1.2 * load) - noise_cssr
    service_drop = 0.5 + (0.8 * load) + noise_drop
    throughput = 55.0 - (12.0 * load) + noise_speed
    traffic = urban_factor * load * noise_traffic

    # --------------------------------------------------------
    # 7.2. QUALITY PROFILE
    # --------------------------------------------------------

    if profile == "medium":
        cssr -= 2.0
        service_drop += 2.5
        throughput -= 36.0

    elif profile == "poor":
        cssr -= 6.0
        service_drop += 6.0
        throughput -= 50.0

    # --------------------------------------------------------
    # 7.3. SHORT INCIDENT
    # --------------------------------------------------------

    # Incident effects are applied in apply_scenarios(),
    # which has access to the full timestamp.

    # --------------------------------------------------------
    # 7.4. BOUNDARY
    # --------------------------------------------------------

    cssr = max(70.0, min(100.0, cssr))
    service_drop = max(0.0, min(30.0, service_drop))
    throughput = max(0.5, throughput)
    traffic = max(0.0, traffic)

    return {
        "cssr": round(cssr, 4),
        "service_drop_all": round(service_drop, 4),
        "user_throughput": round(throughput, 4),
        "traffic": round(traffic, 4),
    }


# ============================================================
# 8. DATA QUALITY SCENARIOS
# ============================================================


def apply_scenarios(
    rng: random.Random,
    cell: str,
    province: str,
    ward: str | None,
    kpi: str,
    ts: datetime,
    value: float,
) -> tuple[float | None, str, str | None]:
    """Apply simulated data-quality and incident scenarios."""

    status = "ok"
    note = None

    # 8.1. Random missing data.
    if rng.random() < 0.0005:
        return None, "missing", None

    # 8.2. Missing data for one province at a fixed hour.
    if ts == START + timedelta(hours=44) and province == MISSING_PROVINCE:
        return None, "missing", None

    # 8.3. Partial missing data in one ward.
    if ts == START + timedelta(hours=44) and kpi == "cssr" and cell == f"HCM-{PARTIAL_WARD}-1":
        return None, "missing", None

    # 8.4. Zero traffic for a selected ward.
    if ts == START + timedelta(hours=44) and kpi == "traffic" and ward == ZERO_TRAFFIC_WARD:
        return 0.0, "ok", None

    # 8.5. Invalid throughput sample.
    if ts == START + timedelta(hours=44) and kpi == "user_throughput" and cell == INVALID_CELL:
        return None, "invalid", "Mau loi gia lap (du lieu thu)"

    # 8.6. Short network incident.
    if INCIDENT_START <= ts < INCIDENT_END and ward == INCIDENT_WARD:
        if kpi == "cssr":
            value -= 8.0
        elif kpi == "service_drop_all":
            value += 8.0
        elif kpi == "user_throughput":
            value *= 0.25

        note = INCIDENT_NOTE

    return round(value, 4), status, note


# ============================================================
# 9. STREAM KPI ROWS
# ============================================================


def iter_rows(
    cells: list[tuple[str, str, str | None]],
    poor_wards: set[str],
):
    """Stream KPI rows instead of keeping all rows in memory.

    Each row:
        (cell_code, kpi_code, period_start, value, status, quality_note)
    """

    rng = random.Random(SEED)

    for h in range(HOURS):
        ts = START + timedelta(hours=h)

        for cell, province, ward in cells:
            profile = get_cell_profile(
                cell=cell,
                province=province,
                ward=ward,
                poor_wards=poor_wards,
            )

            values = simulate_kpis(
                rng=rng,
                hour=ts.hour,
                profile=profile,
                province=province,
                ward=ward,
            )

            for kpi in KPIS:
                value, status, note = apply_scenarios(
                    rng=rng,
                    cell=cell,
                    province=province,
                    ward=ward,
                    kpi=kpi,
                    ts=ts,
                    value=values[kpi],
                )

                yield (cell, kpi, ts, value, status, note)


# ============================================================
# 10. KPI VALUE INSERT
# ============================================================

VALUE_SQL = """
INSERT INTO n46.cell_kpi_values AS existing (
    source_id,
    cell_id,
    kpi_id,
    period_start,
    value,
    status,
    quality_note
)
SELECT
    s.source_id,
    c.cell_id,
    k.kpi_id,
    t.period_start,
    t.value,
    t.status,
    t.quality_note
FROM tmp_values t
JOIN n46.cells c ON c.cell_code = t.cell_code
JOIN n46.kpis k ON k.kpi_code = t.kpi_code
JOIN n46.data_sources s ON s.source_code = %s
ON CONFLICT (source_id, cell_id, kpi_id, period_start)
DO UPDATE SET
    value = EXCLUDED.value,
    status = EXCLUDED.status,
    quality_note = EXCLUDED.quality_note
WHERE
    existing.value IS DISTINCT FROM EXCLUDED.value
    OR existing.status IS DISTINCT FROM EXCLUDED.status
    OR existing.quality_note IS DISTINCT FROM EXCLUDED.quality_note
"""

# ============================================================
# 11. REFRESH MATERIALIZED VIEWS
# ============================================================


def refresh(dsn: str) -> None:
    sql_path = Path(__file__).resolve().parents[2] / "db" / "N4.6_Refresh_Materialized_Views.sql"

    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql_path.read_text(encoding="utf-8"))


# ============================================================
# 12. LOAD DATASET
# ============================================================


def main() -> None:
    dsn = settings.database_url.replace(
        "postgresql+psycopg",
        "postgresql",
    )

    expected_rows = EXPECTED_ROWS

    print("=" * 60)
    print("SIM-4G-2026-10 DATA GENERATOR")
    print("=" * 60)

    print(f"Dataset: {SOURCE}")
    print(f"Period: {START} -> {END}")
    print(f"Hours: {HOURS}")
    print(f"Expected cells: {EXPECTED_CELLS}")
    print(f"Expected KPI rows: {expected_rows:,}")

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        # 12.1. Load regions.
        cur.execute(
            """
            SELECT
                r.region_code,
                r.region_level,
                p.region_code
            FROM n46.regions r
            LEFT JOIN n46.regions p
                ON p.region_id = r.parent_region_id
            """
        )

        regions = cur.fetchall()

        # Validate scenario wards before generating/loading data.
        poor_wards = validate_scenario_wards(regions)

        # 12.2. Generate cell definitions.
        cells = make_cells(regions)

        if len(cells) != EXPECTED_CELLS:
            raise RuntimeError(f"Expected {EXPECTED_CELLS} cells, got {len(cells)}")

        print(f"Cell count: {len(cells)} - PASS")

        # 12.3. Insert missing cells.
        cur.executemany(
            CELL_SQL,
            [(cell, ward, province) for cell, province, ward in cells],
        )

        # 12.4. Upsert source metadata.
        cur.execute(
            SOURCE_SQL,
            {
                "code": SOURCE,
                "start": START,
                "end": END,
                "version": METHOD_VERSION,
                "seed": SEED,
            },
        )

        # 12.5. Create temporary table.
        cur.execute(
            """
            CREATE TEMP TABLE tmp_values (
                cell_code text,
                kpi_code text,
                period_start timestamptz,
                value numeric,
                status text,
                quality_note text
            ) ON COMMIT DROP
            """
        )

        # 12.6. Stream rows directly into COPY.
        with cur.copy("COPY tmp_values FROM STDIN") as copy:
            count = 0

            for row in iter_rows(cells, poor_wards):
                copy.write_row(row)
                count += 1

                if count % 500000 == 0:
                    print(f"Generated and copied: {count:,}")

        if count != expected_rows:
            raise RuntimeError(f"Expected {expected_rows:,} rows, got {count:,}")

        print(f"Generated rows: {count:,} - PASS")

        # 12.7. Insert into official table.
        cur.execute(VALUE_SQL, (SOURCE,))

        print("Database UPSERT: completed")

        # 12.8. Verify actual row count.
        cur.execute(
            """
            SELECT COUNT(*)
            FROM n46.cell_kpi_values
            WHERE source_id = (
                SELECT source_id
                FROM n46.data_sources
                WHERE source_code = %s
            )
            """,
            (SOURCE,),
        )

        actual_rows = cur.fetchone()[0]

        if actual_rows != expected_rows:
            raise RuntimeError(f"Expected {expected_rows:,}, database has {actual_rows:,}")

        print(f"Database rows: {actual_rows:,} - PASS")

    # Refresh after transaction has committed.
    print("Refreshing materialized views...")
    refresh(dsn)

    print("=" * 60)
    print("SIMULATION DATASET LOADED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
