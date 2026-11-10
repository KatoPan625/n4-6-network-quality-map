"""Tao du lieu THU cho Backend: luoi 3x3 o gia lap + KPI gia.

Day KHONG phai bo du lieu demo chinh thuc (phan cua Data/QA).
Chay: uv run python scripts/make_sample_data.py
"""

import csv
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data"
ORIGIN_LON, ORIGIN_LAT, STEP = 106.60, 10.70, 0.05  # o luoi gia lap, khong phai vi tri tram
KPIS = {"latency_ms": (15, 120), "packet_loss_pct": (0.0, 3.0)}
PERIODS = ["2026-09-01", "2026-10-01"]
MISSING = {("R-1-1", "latency_ms", "2026-10-01"), ("R-2-2", "packet_loss_pct", "2026-09-01")}


def make_grid() -> dict:
    features = []
    for row in range(3):
        for col in range(3):
            x0, y0 = ORIGIN_LON + col * STEP, ORIGIN_LAT + row * STEP
            ring = [[x0, y0], [x0 + STEP, y0], [x0 + STEP, y0 + STEP], [x0, y0 + STEP], [x0, y0]]
            code = f"R-{row}-{col}"
            features.append({
                "type": "Feature",
                "properties": {"region_code": code, "name": f"O luoi {row}-{col}", "level": "grid"},
                "geometry": {"type": "MultiPolygon", "coordinates": [[ring]]},
            })
    return {"type": "FeatureCollection", "features": features}


def make_kpi(codes: list[str]) -> list[dict]:
    rng = random.Random(46)  # co dinh seed de tai lap
    rows = []
    for code in codes:
        for kpi, (lo, hi) in KPIS.items():
            for period in PERIODS:
                missing = (code, kpi, period) in MISSING
                rows.append({
                    "region_code": code, "kpi_code": kpi, "period_type": "month",
                    "period_start": period,
                    "value": "" if missing else round(rng.uniform(lo, hi), 2),
                    "status": "missing" if missing else "ok",
                    "source": "simulated-v1",
                })
    return rows


def main() -> None:
    OUT.mkdir(exist_ok=True)
    grid = make_grid()
    (OUT / "sample_grid.geojson").write_text(json.dumps(grid, indent=2), encoding="utf-8")
    codes = [f["properties"]["region_code"] for f in grid["features"]]
    rows = make_kpi(codes)
    with open(OUT / "sample_kpi.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Da tao {len(codes)} vung, {len(rows)} dong KPI trong {OUT}")


if __name__ == "__main__":
    main()
