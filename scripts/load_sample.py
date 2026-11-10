"""Nap du lieu thu (data/) vao PostGIS. Chay lai nhieu lan khong bi trung (upsert).

Chay: uv run python scripts/load_sample.py
"""

import csv
import json
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings

DATA = Path(__file__).resolve().parent.parent / "data"

KPI_DEFS = [
    ("latency_ms", "Do tre (mau)", "ms", "Gia tri mau, cach tinh cho mentor chot", False),
    ("packet_loss_pct", "Ty le mat goi (mau)", "%", "Gia tri mau, cach tinh cho mentor chot", False),
]


def main() -> None:
    dsn = settings.database_url.replace("postgresql+psycopg", "postgresql")
    grid = json.loads((DATA / "sample_grid.geojson").read_text(encoding="utf-8"))
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        for f in grid["features"]:
            p = f["properties"]
            cur.execute(
                "INSERT INTO region (region_code, name, level, geom) "
                "VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)) "
                "ON CONFLICT (region_code) DO UPDATE SET name = EXCLUDED.name, "
                "level = EXCLUDED.level, geom = EXCLUDED.geom",
                (p["region_code"], p["name"], p["level"], json.dumps(f["geometry"])),
            )
        cur.executemany(
            "INSERT INTO kpi_definition VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, unit = EXCLUDED.unit, "
            "description = EXCLUDED.description, higher_is_better = EXCLUDED.higher_is_better",
            KPI_DEFS,
        )
        with open(DATA / "sample_kpi.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        cur.executemany(
            "INSERT INTO kpi_value (region_code, kpi_code, period_type, period_start, "
            "value, status, source) VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (region_code, kpi_code, period_type, period_start) DO UPDATE SET "
            "value = EXCLUDED.value, status = EXCLUDED.status, source = EXCLUDED.source, "
            "updated_at = now()",
            [
                (r["region_code"], r["kpi_code"], r["period_type"], r["period_start"],
                 float(r["value"]) if r["value"] else None, r["status"], r["source"])
                for r in rows
            ],
        )
    print(f"Da nap {len(grid['features'])} vung, {len(KPI_DEFS)} KPI, {len(rows)} gia tri")


if __name__ == "__main__":
    main()
