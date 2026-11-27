"""Do thoi gian phan hoi API o quy mo lab (baseline, KHONG phai chi tieu nghiem thu).

Can server dang chay (uv run uvicorn app.main:app) va CSDL da nap SIM-4G-2026-10
(uv run python scripts/generate_simulation.py).
Chay: uv run python scripts/bench_api.py [so_lan]
"""

import platform
import statistics
import sys
import time
from datetime import datetime

import httpx

BASE = "http://localhost:8000"
SOURCE = "SIM-4G-2026-10"
CASES = [
    ("GET /regions (34 tinh)", "/api/v1/regions", {}),
    ("GET /regions?level=ward", "/api/v1/regions", {"level": "ward"}),
    (
        "GET /kpi-values (gio, phuong)",
        "/api/v1/kpi-values",
        {"kpi": "cssr", "level": "ward", "at": "2026-10-15T20:00"},
    ),
    (
        "GET /kpi-values (ngay, phuong)",
        "/api/v1/kpi-values",
        {"kpi": "cssr", "level": "ward", "at": "2026-10-15", "period_type": "day"},
    ),
    ("GET /regions/79/kpis (720 gio)", "/api/v1/regions/79/kpis", {"period_type": "hour"}),
    ("GET /regions/79/kpis (30 ngay)", "/api/v1/regions/79/kpis", {}),
    (
        "GET /compare (ngay, tinh)",
        "/api/v1/compare",
        {"kpi": "cssr", "a": "2026-10-01", "b": "2026-10-30"},
    ),
]


def pct(data: list[float], p: float) -> float:
    s = sorted(data)
    return s[min(len(s) - 1, round(p * (len(s) - 1)))]


def check_data(client: httpx.Client) -> None:
    """Dung som neu nguon mac dinh khong phai SIM-4G hoac chua co du lieu (API van tra 200)."""
    res = client.get(
        "/api/v1/kpi-values", params={"kpi": "cssr", "level": "ward", "at": "2026-10-15T20:00"}
    )
    body = res.json() if res.status_code == 200 else {"source": {}, "items": []}
    if body["source"].get("source_code") != SOURCE or not any(
        i["status"] == "ok" for i in body["items"]
    ):
        sys.exit(f"Nguon mac dinh chua co du lieu {SOURCE}: chay scripts/generate_simulation.py")


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    print(f"Baseline API - {datetime.now():%Y-%m-%d %H:%M} - {platform.node()} - {n} lan/endpoint")
    print(f"Du lieu: 34 tinh + 168 phuong, 996 cell, 4 KPI, 720 gio ({SOURCE}). Server local.\n")
    print(f"{'Endpoint':34} {'p50 ms':>8} {'p95 ms':>8} {'max ms':>8} {'loi':>4}")
    with httpx.Client(base_url=BASE, timeout=10) as client:
        check_data(client)
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
