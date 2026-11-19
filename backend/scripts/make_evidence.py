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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.load_sample import CASE_HOUR, PARTIAL_WARD, ZERO_TRAFFIC_WARD

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "evidence"
TMP = EV / "_html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE = "http://localhost:8000"
DAY = date.today().isoformat()
SRC = "BE-SAMPLE"
HOUR_CASE = CASE_HOUR.strftime("%Y-%m-%dT%H:%M")
DAY_CASE = CASE_HOUR.date().isoformat()
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
        [
            EDGE,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={width},{height}",
            f"--screenshot={out}",
            src.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    print("Da tao", out.name)


def log_page(name: str, title: str, log_file: str, tail: int | None = None) -> None:
    raw = (EV / log_file).read_bytes()
    text = (
        raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    )
    lines = text.rstrip().splitlines()[-tail:] if tail else text.rstrip().splitlines()
    body = f"<pre>{html.escape(chr(10).join(lines))}</pre>"
    page(name, title, f"Nguon: evidence/{log_file} - {DAY}", body, 1100, 120 + 19 * len(lines))


def color(v: float, lo: float, hi: float, higher_is_better: bool) -> str:
    t = 0.5 if hi == lo else (v - lo) / (hi - lo)
    t = t if higher_is_better else 1 - t  # t=1 la tot
    return f"hsl({round(t * 120)},65%,55%)"


def ward_map_preview(client: httpx.Client) -> None:
    params = {"kpi": "cssr", "level": "ward", "period_type": "day", "at": DAY_CASE, "source": SRC}
    regions = client.get("/api/v1/regions", params={"level": "ward", "simplify": 0.002}).json()
    kv = client.get("/api/v1/kpi-values", params=params).json()
    vals = {i["region_code"]: i for i in kv["items"]}
    ok = [i["value"] for i in kv["items"] if i["value"] is not None]
    lo, hi = min(ok), max(ok)
    rings = {
        f["id"]: [ring[0] for ring in f["geometry"]["coordinates"]] for f in regions["features"]
    }
    xs = [x for rs in rings.values() for r in rs for x, _ in r]
    ys = [y for rs in rings.values() for r in rs for _, y in r]
    size = 640
    scale = size / max(max(xs) - min(xs), max(ys) - min(ys))

    def pt(p):
        return (p[0] - min(xs)) * scale, (max(ys) - p[1]) * scale

    shapes = []
    for code, rs in rings.items():
        item = vals[code]
        fill = "url(#hatch)" if item["value"] is None else color(item["value"], lo, hi, True)
        dash = " stroke-dasharray='4 3' stroke='#111'" if item["status"] == "partial" else ""
        for r in rs:
            poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(pt, r))
            shapes.append(
                f"<polygon points='{poly}' fill='{fill}' stroke='#fff' stroke-width='1'{dash}/>"
            )
    svg = (
        f"<svg width='{size}' height='{size}'>"
        "<defs><pattern id='hatch' width='8' height='8' patternUnits='userSpaceOnUse' "
        "patternTransform='rotate(45)'><rect width='8' height='8' fill='#e5e7eb'/>"
        "<line x1='0' y1='0' x2='0' y2='8' stroke='#9ca3af' stroke-width='3'/></pattern></defs>"
        + "".join(shapes)
        + "</svg>"
    )
    legend = (
        f"<p class='sub' style='margin-top:10px'>CSSR ngay {DAY_CASE}: xanh = cao (tot), do = thap. "
        "Gach cheo = khong tinh duoc gia tri; vien net dut = partial (thieu mot phan cell).</p>"
    )
    page(
        "e2e_ward_map_preview",
        f"Kiem tra luong CSDL -> API: CSSR 168 phuong/xa TP.HCM, ngay {DAY_CASE}",
        "Anh kiem tra du lieu cua Backend (khong phai giao dien Frontend). Du lieu thu BE-SAMPLE.",
        svg + legend,
        720,
        800,
    )


def json_page(client: httpx.Client) -> None:
    res = client.get(
        "/api/v1/kpi-values",
        params={
            "kpi": "cssr",
            "level": "ward",
            "at": HOUR_CASE,
            "source": SRC,
            "region": [PARTIAL_WARD, ZERO_TRAFFIC_WARD],
        },
    )
    body = json.dumps(res.json(), indent=2, ensure_ascii=False)
    url = str(res.request.url).replace(BASE, "")
    page(
        "api_kpi_values_partial",
        f"GET {url}",
        f"HTTP {res.status_code} - phuong partial va phuong khong co traffic duong",
        f"<pre>{html.escape(body)}</pre>",
        1000,
        120 + 19 * len(body.splitlines()),
    )


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=10) as client:
        client.get("/health").raise_for_status()
        ward_map_preview(client)
        json_page(client)
    subprocess.run(
        [
            EDGE,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1400,1150",
            "--virtual-time-budget=8000",
            f"--screenshot={EV / f'{DAY}_swagger_docs.png'}",
            f"{BASE}/docs",
        ],
        check=True,
        capture_output=True,
    )
    print("Da tao", f"{DAY}_swagger_docs.png")
    log_page("pytest", "Kiem thu tu dong: uv run pytest -v", "pytest_run.txt")
    log_page("bruno_run", "Kiem thu API bang Bruno CLI", "bruno_run.txt")
    log_page("bench_baseline", "Baseline thoi gian phan hoi API (quy mo lab)", "bench_baseline.txt")
    log_page("git_log", "Lich su commit", "git_log.txt")


if __name__ == "__main__":
    sys.exit(main())
