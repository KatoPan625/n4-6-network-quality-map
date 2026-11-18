"""Tao du lieu THU cho Backend theo schema V2.1: 165 o x 8 KPI x 2 tuan, nguon BE-SAMPLE.

Day KHONG phai bo du lieu mo phong chinh thuc SIM-V1 (phan cua Vu).
O luoi lay tu khung HCM-CENTER-NE trong schema: i = 683..697, j = 1190..1200.
Chay: uv run python scripts/make_sample_data.py
"""

import csv
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data"
SOURCE = "BE-SAMPLE"
WEEKS = ["2026-10-19", "2026-10-26"]  # 2 tuan cuoi cua ky mo phong, deu la thu Hai
CODES = [f"G1K-{i}-{j}" for i in range(683, 698) for j in range(1190, 1201)]

# KPI khong phai ti le: (min, max) cua gia tri
PLAIN = {
    "download_throughput": (50, 900),
    "upload_throughput": (30, 800),
    "latency": (3, 60),
    "jitter": (0.5, 15),
}
# KPI ti le: (mau so min, mau so max, ti le tu/mau toi da) -> value = tu / mau x 100
RATIO = {
    "packet_loss_rate": (50_000, 200_000, 0.02),
    "network_availability": (604_800, 604_800, 1.0),  # giay trong 1 tuan
    "http_ip_access_failure_ratio": (1_000, 5_000, 0.03),
    "http_dropped_sessions_ratio": (1_000, 5_000, 0.03),
}

# Cac o co y de trong / sai de test (xem tests/test_kpi_api.py)
MISSING_ROW = ("G1K-690-1195", "latency", WEEKS[1])  # co dong, status missing
NO_ROW = ("G1K-683-1190", "latency", WEEKS[1])  # khong co dong nao
INVALID = ("G1K-697-1200", "packet_loss_rate", WEEKS[0])


def make_rows() -> list[dict]:
    rng = random.Random(46)  # co dinh seed de tai lap
    rows = []
    for code in CODES:
        for kpi in [*PLAIN, *RATIO]:
            for week in WEEKS:
                key = (code, kpi, week)
                if key == NO_ROW:
                    continue
                row = {
                    "source_code": SOURCE,
                    "region_code": code,
                    "kpi_code": kpi,
                    "period_start": week,
                    "value": "",
                    "status": "ok",
                    "sample_count": rng.randint(20, 500),
                    "numerator_value": "",
                    "denominator_value": "",
                    "quality_note": "",
                }
                if key == MISSING_ROW:
                    row.update(status="missing", sample_count=0)
                elif key == INVALID:
                    row.update(
                        status="invalid", quality_note="Mau loi do thiet bi do (du lieu thu)"
                    )
                elif kpi in PLAIN:
                    lo, hi = PLAIN[kpi]
                    row["value"] = round(rng.uniform(lo, hi), 2)
                else:
                    dmin, dmax, max_ratio = RATIO[kpi]
                    d = rng.randint(dmin, dmax)
                    bad = rng.randint(
                        0, int(d * (0.01 if kpi == "network_availability" else max_ratio))
                    )
                    n = d - bad if kpi == "network_availability" else bad
                    row.update(value=round(n / d * 100, 6), numerator_value=n, denominator_value=d)
                rows.append(row)
    return rows


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rows = make_rows()
    with open(OUT / "sample_kpi.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Da tao {len(CODES)} o, {len(rows)} dong KPI trong {OUT}")


if __name__ == "__main__":
    main()
