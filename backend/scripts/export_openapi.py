"""Xuat docs/openapi.json de Frontend dung (mock, sinh client). Khong can CSDL.

Chay: uv run python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.main import app

out = ROOT / "docs" / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Da xuat {len(app.openapi()['paths'])} path vao {out}")
