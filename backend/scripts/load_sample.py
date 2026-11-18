"""Nap du lieu thu (data/sample_kpi.csv) vao CSDL schema V2.1. Chay lai nhieu lan khong trung (upsert).

O luoi, KPI va nguon SIM-V1 da co san tu file schema. Script nay chi them nguon BE-SAMPLE
(is_default = FALSE, khong dung chung voi SIM-V1 cua Vu) va gia tri KPI cua nguon do.
Chay: uv run python scripts/load_sample.py
"""

import csv
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings

DATA = Path(__file__).resolve().parent.parent / "data"

SOURCE_SQL = """
INSERT INTO data_sources (source_code, source_name, source_type, data_nature, description,
    spatial_scope, period_from, period_to, collection_method, method_version, random_seed,
    assumptions, limitations, is_default)
VALUES ('BE-SAMPLE', 'Du lieu thu cua Backend', 'simulation', 'simulated',
    'Gia tri ngau nhien deu de test API; 2 tuan cuoi ky.',
    'Khung HCM-CENTER-NE, luoi 1 km.', DATE '2026-05-04', DATE '2026-11-01',
    'scripts/make_sample_data.py: random.uniform trong khoang co dinh moi KPI.', 'be-sample-1', 46,
    'Khong co gia dinh nghiep vu; chi de kiem thu.',
    'Chi dung de test Backend; khong dung de ve ban do hay bao cao.', FALSE)
ON CONFLICT (source_code) DO NOTHING
"""

VALUE_SQL = """
INSERT INTO kpi_values (source_id, region_id, kpi_id, period_start, value, status, sample_count,
    numerator_value, denominator_value, quality_note)
SELECT s.source_id, r.region_id, k.kpi_id, %(period_start)s, %(value)s, %(status)s,
    %(sample_count)s, %(numerator_value)s, %(denominator_value)s, %(quality_note)s
FROM data_sources s, regions r, kpis k
WHERE s.source_code = %(source_code)s AND r.region_code = %(region_code)s
  AND k.kpi_code = %(kpi_code)s
ON CONFLICT (source_id, kpi_id, period_start, region_id) DO UPDATE SET
    value = EXCLUDED.value, status = EXCLUDED.status, sample_count = EXCLUDED.sample_count,
    numerator_value = EXCLUDED.numerator_value, denominator_value = EXCLUDED.denominator_value,
    quality_note = EXCLUDED.quality_note
"""


def main() -> None:
    dsn = settings.database_url.replace("postgresql+psycopg", "postgresql")
    with open(DATA / "sample_kpi.csv", encoding="utf-8") as fh:
        # o trong trong CSV -> NULL
        rows = [{k: (v or None) for k, v in r.items()} for r in csv.DictReader(fh)]
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(SOURCE_SQL)
        cur.executemany(VALUE_SQL, rows)
        cur.execute(
            "SELECT count(*) FROM kpi_values v JOIN data_sources s USING (source_id) "
            "WHERE s.source_code = 'BE-SAMPLE'"
        )
        loaded = cur.fetchone()[0]
    if loaded != len(rows):  # ma o/KPI trong CSV khong khop CSDL thi SELECT tren tra 0 dong
        sys.exit(f"Loi: CSV co {len(rows)} dong nhung CSDL chi co {loaded} dong cua BE-SAMPLE")
    print(f"Da nap {loaded} gia tri KPI cho nguon BE-SAMPLE")


if __name__ == "__main__":
    main()
