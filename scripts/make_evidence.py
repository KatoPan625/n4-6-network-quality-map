"""Tao anh minh chung cho bao cao tu log va API dang chay (Windows + Edge).

Chay: uv run python scripts/make_evidence.py   (can server + CSDL dang chay)
"""

import html
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "evidence"
TMP = EV / "_html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE = "http://localhost:8000"
DAY = date.today().isoformat()
CSS = (
    "body{font-family:Segoe UI,Arial;margin:24px;background:#fff;color:#1b1b1b}"
    "h1{font-size:20px;margin:0 0 4px}p.sub{color:#555;margin:0 0 14px;font-size:13px}"
    "pre{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;font:13px Consolas,monospace;"
    "white-space:pre-wrap;margin:0}"
)


def page(name: str, title: str, sub: str, body: str, width: int, height: int) -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    src = TMP / f"{name}.html"
    src.write_text(
        f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
        f"<h1>{html.escape(title)}</h1><p class='sub'>{html.escape(sub)}</p>{body}",
        encoding="utf-8",
    )
    out = EV / f"{DAY}_{name}.png"
    subprocess.run(
        [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         f"--window-size={width},{height}", f"--screenshot={out}", src.as_uri()],
        check=True, capture_output=True,
    )
    print("Da tao", out.name)


def log_page(name: str, title: str, log_file: str, tail: int | None = None) -> None:
    raw = (EV / log_file).read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    lines = text.rstrip().splitlines()[-tail:] if tail else text.rstrip().splitlines()
    body = f"<pre>{html.escape(chr(10).join(lines))}</pre>"
    page(name, title, f"Nguon: evidence/{log_file} - {DAY}", body, 1100, 120 + 19 * len(lines))


def color(v: float, lo: float, hi: float, higher_is_better: bool) -> str:
    t = 0.5 if hi == lo else (v - lo) / (hi - lo)
    t = t if higher_is_better else 1 - t  # t=1 la tot
    return f"hsl({round(t * 120)},65%,55%)"


def grid_preview(client: httpx.Client) -> None:
    params = {"kpi": "latency_ms", "period_start": "2026-10-01"}
    regions = client.get("/api/v1/regions").json()["features"]
    kv = client.get("/api/v1/kpi-values", params=params).json()
    vals = {i["region_code"]: i for i in kv["items"]}
    ok = [i["value"] for i in kv["items"] if i["status"] == "ok"]
    lo, hi = min(ok), max(ok)
    xs = [p[0] for f in regions for p in f["geometry"]["coordinates"][0][0]]
    ys = [p[1] for f in regions for p in f["geometry"]["coordinates"][0][0]]
    sx, sy, size = min(xs), max(ys), 480

    def pt(p):
        return (p[0] - sx) / (max(xs) - sx) * size, (sy - p[1]) / (sy - min(ys)) * size

    shapes = []
    for f in regions:
        ring = [pt(p) for p in f["geometry"]["coordinates"][0][0]]
        code = f["properties"]["region_code"]
        item = vals[code]
        fill = "url(#hatch)" if item["value"] is None else color(item["value"], lo, hi, False)
        label = "thieu du lieu" if item["value"] is None else f"{item['value']} {kv['kpi']['unit']}"
        cx = sum(x for x, _ in ring[:-1]) / 4
        cy = sum(y for _, y in ring[:-1]) / 4
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in ring)
        shapes.append(
            f"<polygon points='{poly}' fill='{fill}' stroke='#fff' stroke-width='3'/>"
            f"<text x='{cx}' y='{cy - 6}' text-anchor='middle' font-size='14' font-weight='600'>{code}</text>"
            f"<text x='{cx}' y='{cy + 14}' text-anchor='middle' font-size='13'>{label}</text>"
        )
    svg = (
        f"<svg width='{size}' height='{size}' style='font-family:Segoe UI'>"
        "<defs><pattern id='hatch' width='8' height='8' patternUnits='userSpaceOnUse' "
        "patternTransform='rotate(45)'><rect width='8' height='8' fill='#e5e7eb'/>"
        "<line x1='0' y1='0' x2='0' y2='8' stroke='#9ca3af' stroke-width='3'/></pattern></defs>"
        + "".join(shapes) + "</svg>"
    )
    legend = (
        "<p class='sub' style='margin-top:10px'>Xanh = do tre thap (tot), do = cao. "
        "Gach cheo = thieu du lieu (API tra null + status missing, khong phai 0).</p>"
    )
    page("e2e_grid_preview", "Kiem tra luong CSDL -> API: latency_ms, thang 10/2026",
         "Anh kiem tra du lieu cua Backend (khong phai giao dien Frontend). Du lieu thu, luoi gia lap.",
         svg + legend, 560, 720)


def json_page(client: httpx.Client) -> None:
    res = client.get("/api/v1/kpi-values",
                     params={"kpi": "latency_ms", "period_start": "2026-10-01",
                             "region": ["R-0-0", "R-1-1"]})
    body = json.dumps(res.json(), indent=2, ensure_ascii=False)
    url = str(res.request.url).replace(BASE, "")
    page("api_kpi_values_missing", f"GET {url}", f"HTTP {res.status_code} - R-1-1 thieu du lieu",
         f"<pre>{html.escape(body)}</pre>", 1000, 120 + 19 * len(body.splitlines()))


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=10) as client:
        client.get("/health").raise_for_status()
        grid_preview(client)
        json_page(client)
    subprocess.run(
        [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1400,1150",
         "--virtual-time-budget=8000", f"--screenshot={EV / f'{DAY}_swagger_docs.png'}",
         f"{BASE}/docs"], check=True, capture_output=True,
    )
    print("Da tao", f"{DAY}_swagger_docs.png")
    log_page("pytest", "Kiem thu tu dong: uv run pytest -v", "pytest_run.txt")
    log_page("bruno_run", "Kiem thu API bang Bruno CLI (8 request)", "bruno_run.txt")
    log_page("bench_baseline", "Baseline thoi gian phan hoi API (quy mo lab)", "bench_baseline.txt")
    log_page("git_log", "Lich su commit", "git_log.txt")


if __name__ == "__main__":
    sys.exit(main())
