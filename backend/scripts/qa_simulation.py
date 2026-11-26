
"""QA checks for SIM-4G-2026-10."""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings


# ============================================================
# 1. CONFIGURATION
# ============================================================

VN = ZoneInfo("Asia/Ho_Chi_Minh")

SOURCE = "SIM-4G-2026-10"

EXPECTED_CELLS = 996
EXPECTED_HOURS = 720
EXPECTED_KPIS = 4
EXPECTED_ROWS = EXPECTED_CELLS * EXPECTED_HOURS * EXPECTED_KPIS

START = datetime(2026, 10, 1, 0, 0, tzinfo=VN)
END = datetime(2026, 10, 31, 0, 0, tzinfo=VN)

INCIDENT_WARD = "25750"
INCIDENT_START = datetime(2026, 10, 15, 20, 0, tzinfo=VN)
INCIDENT_END = datetime(2026, 10, 15, 23, 0, tzinfo=VN)

INCIDENT_NOTE = "SIMULATED_INCIDENT_2026-10-15"

dsn = settings.database_url.replace(
    "postgresql+psycopg", "postgresql"
)

checks = []


def check(name, condition, detail=""):
    passed = bool(condition)
    checks.append(passed)

    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {detail}")


# ============================================================
# 2. DATABASE QA
# ============================================================

with psycopg.connect(dsn) as conn:

    with conn.cursor() as cur:

        # ----------------------------------------------------
        # 2.1. Cell count
        # ----------------------------------------------------

        cur.execute("SELECT COUNT(*) FROM n46.cells")
        cell_count = cur.fetchone()[0]

        check(
            "Cell count",
            cell_count == EXPECTED_CELLS,
            f"({cell_count}/{EXPECTED_CELLS})",
        )

        # ----------------------------------------------------
        # 2.2. Dataset row count
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            WHERE s.source_code = %s
            """,
            (SOURCE,),
        )

        row_count = cur.fetchone()[0]

        check(
            "Dataset row count",
            row_count == EXPECTED_ROWS,
            f"({row_count:,}/{EXPECTED_ROWS:,})",
        )

        # ----------------------------------------------------
        # 2.3. Unique cells in dataset
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(DISTINCT v.cell_id)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            WHERE s.source_code = %s
            """,
            (SOURCE,),
        )

        dataset_cells = cur.fetchone()[0]

        check(
            "Dataset unique cells",
            dataset_cells == EXPECTED_CELLS,
            f"({dataset_cells}/{EXPECTED_CELLS})",
        )

        # ----------------------------------------------------
        # 2.4. Unique timestamps
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(DISTINCT v.period_start),
                   MIN(v.period_start),
                   MAX(v.period_start)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            WHERE s.source_code = %s
            """,
            (SOURCE,),
        )

        hours, min_time, max_time = cur.fetchone()

        expected_min = START.astimezone(ZoneInfo("UTC"))
        expected_max = (
            END - timedelta(hours=1)
        ).astimezone(ZoneInfo("UTC"))

        check(
            "Hourly timestamps",
            hours == EXPECTED_HOURS,
            f"({hours}/{EXPECTED_HOURS})",
        )

        check(
            "Start timestamp",
            min_time == expected_min,
            f"({min_time})",
        )

        check(
            "End timestamp",
            max_time == expected_max,
            f"({max_time})",
        )

        # ----------------------------------------------------
        # 2.5. Status distribution
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT v.status, COUNT(*)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            WHERE s.source_code = %s
            GROUP BY v.status
            """,
            (SOURCE,),
        )

        statuses = dict(cur.fetchall())

        check(
            "Missing records exist",
            statuses.get("missing", 0) > 0,
            f"({statuses.get('missing', 0):,})",
        )

        check(
            "Invalid records exist",
            statuses.get("invalid", 0) > 0,
            f"({statuses.get('invalid', 0):,})",
        )

        # ----------------------------------------------------
        # 2.6. Invalid records must have quality_note
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            WHERE s.source_code = %s
              AND v.status = 'invalid'
              AND v.quality_note IS NULL
            """,
            (SOURCE,),
        )

        invalid_without_note = cur.fetchone()[0]

        check(
            "Invalid note constraint",
            invalid_without_note == 0,
            f"({invalid_without_note})",
        )

        # ----------------------------------------------------
        # 2.7. Missing and invalid values must be NULL
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            WHERE s.source_code = %s
              AND v.status IN ('missing', 'invalid')
              AND v.value IS NOT NULL
            """,
            (SOURCE,),
        )

        bad_null_records = cur.fetchone()[0]

        check(
            "Missing/invalid values are NULL",
            bad_null_records == 0,
            f"({bad_null_records})",
        )

        # ----------------------------------------------------
        # 2.8. KPI quality distribution
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT k.kpi_code, v.value, COUNT(*)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            JOIN n46.kpis k USING (kpi_id)
            WHERE s.source_code = %s
              AND v.status = 'ok'
              AND v.value IS NOT NULL
            GROUP BY k.kpi_code, v.value
            """,
            (SOURCE,),
        )

        values = cur.fetchall()

        thresholds = {
            "cssr": (
                lambda x: x >= 98,
                lambda x: 95 <= x < 98,
                lambda x: x < 95,
            ),
            "service_drop_all": (
                lambda x: x <= 2,
                lambda x: 2 < x <= 5,
                lambda x: x > 5,
            ),
            "user_throughput": (
                lambda x: x >= 16,
                lambda x: 5 <= x < 16,
                lambda x: x < 5,
            ),
        }

        for kpi, rules in thresholds.items():

            counts = [0, 0, 0]

            for code, value, amount in values:

                if code != kpi:
                    continue

                for index, rule in enumerate(rules):
                    if rule(float(value)):
                        counts[index] += amount

            for label, amount in zip(
                ("Good", "Medium", "Poor"), counts
            ):
                check(
                    f"{kpi} {label}",
                    amount > 0,
                    f"({amount:,})",
                )

        # ----------------------------------------------------
        # 2.9. Zero traffic
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            JOIN n46.kpis k USING (kpi_id)
            WHERE s.source_code = %s
              AND k.kpi_code = 'traffic'
              AND v.value = 0
              AND v.status = 'ok'
            """,
            (SOURCE,),
        )

        zero_traffic = cur.fetchone()[0]

        check(
            "Zero traffic",
            zero_traffic > 0,
            f"({zero_traffic:,})",
        )

        # ----------------------------------------------------
        # 2.10. Incident scenario
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*)
            FROM n46.cell_kpi_values v
            JOIN n46.data_sources s USING (source_id)
            JOIN n46.cells c USING (cell_id)
            JOIN n46.kpis k USING (kpi_id)
            WHERE s.source_code = %s
              AND c.ward_id IN (
                  SELECT region_id
                  FROM n46.regions
                  WHERE region_code = %s
              )
              AND v.period_start >= %s
              AND v.period_start < %s
              AND v.quality_note = %s
            """,
            (
                SOURCE,
                INCIDENT_WARD,
                INCIDENT_START.astimezone(ZoneInfo("UTC")),
                INCIDENT_END.astimezone(ZoneInfo("UTC")),
                INCIDENT_NOTE,
            ),
        )

        incident_records = cur.fetchone()[0]

        check(
            "Incident scenario",
            incident_records > 0,
            f"({incident_records:,})",
        )

        # ----------------------------------------------------
        # 2.11. Metadata
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT data_nature,
                   source_type,
                   timezone_name,
                   method_version,
                   random_seed,
                   period_from,
                   period_to
            FROM n46.data_sources
            WHERE source_code = %s
            """,
            (SOURCE,),
        )

        metadata = cur.fetchone()

        check("Source metadata exists", metadata is not None)

        if metadata:
            (
                data_nature,
                source_type,
                timezone_name,
                method_version,
                random_seed,
                period_from,
                period_to,
            ) = metadata

            check("Synthetic data nature", data_nature == "simulated")
            check("Simulation source type", source_type == "simulation")
            check("Timezone", timezone_name == "Asia/Ho_Chi_Minh")
            check("Method version", method_version == "sim-4g-v1.0")
            check("Random seed", random_seed == 202610)
            check("Metadata start", period_from == expected_min)
            check("Metadata end", period_to == END.astimezone(ZoneInfo("UTC")))


# ============================================================
# 3. FINAL RESULT
# ============================================================

print("=" * 60)
print(f"QA RESULT: {'PASS' if all(checks) else 'FAIL'}")
print(f"Passed: {sum(checks)}/{len(checks)}")
print("=" * 60)

if not all(checks):
    sys.exit(1)
