"""Do thoi gian phan hoi API o quy mo lab (baseline, KHONG phai chi tieu nghiem thu).

Can server dang chay: uv run uvicorn app.main:app
Chay: uv run python scripts/bench_api.py [so_lan]
"""

import platform
import statistics
import sys
import time
from datetime import datetime

import httpx

BASE = "http://localhost:8000"
CASES = [
    ("GET /api/v1/regions", "/api/v1/regions", {}),
    (
        "GET /api/v1/kpi-values",
        "/api/v1/kpi-values",
        {"kpi": "latency", "period_start": "2026-10-26", "source": "BE-SAMPLE"},
    ),
    (
        "GET /api/v1/regions/{code}/kpis",
        "/api/v1/regions/G1K-690-1195/kpis",
        {"source": "BE-SAMPLE"},
    ),
    (
        "GET /api/v1/compare",
        "/api/v1/compare",
        {
            "kpi": "latency",
            "period_a": "2026-10-19",
            "period_b": "2026-10-26",
            "source": "BE-SAMPLE",
        },
    ),
]


def pct(data: list[float], p: float) -> float:
    s = sorted(data)
    return s[min(len(s) - 1, round(p * (len(s) - 1)))]


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    print(f"Baseline API - {datetime.now():%Y-%m-%d %H:%M} - {platform.node()} - {n} lan/endpoint")
    print(
        "Du lieu: 165 o 1 km, 8 KPI, 2 tuan (nguon BE-SAMPLE). Server local, 1 worker, 1 client.\n"
    )
    print(f"{'Endpoint':34} {'p50 ms':>8} {'p95 ms':>8} {'max ms':>8} {'loi':>4}")
    with httpx.Client(base_url=BASE, timeout=10) as client:
        for name, path, params in CASES:
            client.get(path, params=params)  # khoi dong
            times, errors = [], 0
            for _ in range(n):
                t0 = time.perf_counter()
                res = client.get(path, params=params)
                times.append((time.perf_counter() - t0) * 1000)
                errors += res.status_code != 200
            print(
                f"{name:34} {statistics.median(times):8.1f} {pct(times, 0.95):8.1f} "
                f"{max(times):8.1f} {errors:4d}"
            )


if __name__ == "__main__":
    main()
