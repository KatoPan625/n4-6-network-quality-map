"""Nap ranh gioi hanh chinh vao n46.regions: 34 tinh/thanh + 168 phuong/xa TP.HCM (sau 01/07/2025).

Nguon: Hugging Face myleo198/sapnhap-bando-vn (trich tu sapnhap.bando.com.vn, Bo NN&MT), CC BY-NC 4.0.
File tai ve data/raw/ (khong commit). Chay lai nhieu lan khong trung (upsert theo region_code).
Phai nap regions TRUOC cells (trigger cua schema chan thu tu nguoc lai).
Chay: uv run python scripts/load_regions.py
"""

import json
import sys
import urllib.request
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
BASE_URL = "https://huggingface.co/datasets/myleo198/sapnhap-bando-vn/resolve/main/geo/"
HCM_CODE = "79"
EXPECTED = {"province": 34, "ward": 168}

# GeoJSON nguon co the co polygon khong hop le; schema CHECK ST_IsValid nen sua truoc khi luu
GEOM_SQL = (
    "ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)), 3))"
)
UPSERT_SQL = f"""
INSERT INTO n46.regions (region_code, region_name, region_level, parent_region_id, geom)
VALUES (%s, %s, %s, (SELECT region_id FROM n46.regions WHERE region_code = %s), {GEOM_SQL})
ON CONFLICT (region_code) DO UPDATE SET region_name = EXCLUDED.region_name, geom = EXCLUDED.geom
"""


def features(name: str) -> list[dict]:
    path = RAW / f"{name}.geojson"
    if not path.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        print(f"Tai {name}.geojson ...")
        urllib.request.urlretrieve(BASE_URL + f"{name}.geojson", path)
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def main() -> None:
    provinces = features("provinces")
    wards = [f for f in features("communes") if f["properties"]["parent_ma"] == HCM_CODE]
    rows = [(f, "province", None) for f in provinces] + [(f, "ward", HCM_CODE) for f in wards]
    dsn = settings.database_url.replace("postgresql+psycopg", "postgresql")
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        for f, level, parent in rows:  # tinh truoc, phuong sau (phuong can region_id cua tinh)
            p = f["properties"]
            cur.execute(UPSERT_SQL, (p["ma"], p["ten"], level, parent, json.dumps(f["geometry"])))
        cur.execute("SELECT region_level, count(*) FROM n46.regions GROUP BY 1")
        counts = dict(cur.fetchall())
    if counts != EXPECTED:
        sys.exit(f"Loi: so vung {counts}, ky vong {EXPECTED}")
    print(f"Da nap {counts['province']} tinh/thanh va {counts['ward']} phuong/xa TP.HCM")


if __name__ == "__main__":
    main()
