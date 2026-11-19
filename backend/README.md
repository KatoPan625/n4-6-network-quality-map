# N4.6 – Backend

Backend/API (FastAPI + PostgreSQL/PostGIS) cho đề tài "Xây dựng bản đồ số hiển thị chất lượng mạng theo khu vực".
CSDL dùng schema chính thức của nhóm (`../db/N4.6_Database_Schema.sql`, schema PostgreSQL `n46`; thiết kế ở `../docs/SCHEMA.md`): mạng di động 4G, KPI theo cell, tổng hợp lên 34 tỉnh/thành và 168 phường/xã TP.HCM, theo giờ/ngày. Dữ liệu thử của Backend là nguồn `BE-SAMPLE`, không phải bộ mô phỏng chính thức `SIM-4G-2026-10`.

## Yêu cầu
Docker Desktop (đang chạy), [uv](https://docs.astral.sh/uv/), Python 3.13.

## Chạy lần đầu
```powershell
copy .env.example .env          # rồi đổi DB_PASSWORD
docker compose up -d --wait     # tạo CSDL + schema (4 KPI, nguồn SIM-4G-2026-10 rỗng)
uv sync
uv run python scripts/load_regions.py  # tải GeoJSON (khoảng 180 MB, vào data/raw/) và nạp 34 tỉnh + 168 phường
uv run python scripts/load_sample.py   # sinh + nạp BE-SAMPLE (996 cell × 4 KPI × 72 giờ), refresh MV
uv run uvicorn app.main:app --reload
```
Mở http://localhost:8000/docs để thử API.

## Kiểm thử
```powershell
uv run pytest -q
uv run ruff check .
```

## Cấu trúc
| Thư mục | Nội dung |
|---|---|
| `app/` | Mã FastAPI (`main.py`, cấu hình, kết nối CSDL) |
| `../db/` | Schema (Docker nạp khi tạo CSDL lần đầu) và script refresh materialized view |
| `scripts/` | Nạp ranh giới, sinh và nạp dữ liệu thử, công cụ đo |
| `data/raw/` | GeoJSON ranh giới tải về (không commit) |
| `docs/api-contract.md` | Hợp đồng API bản nháp |
| `tests/` | Test API (cần CSDL đang chạy) |

## Làm lại CSDL từ đầu
Schema chỉ chạy khi volume trống: `docker compose down -v` (xóa toàn bộ dữ liệu trong CSDL local) rồi chạy lại các bước trên.

Đã có CSDL từ trước: chạy thẳng file schema (tạo trong schema `n46`, chạy lại nhiều lần không lỗi):
`docker exec -i n46-postgis psql -U n46 -d n46 -v ON_ERROR_STOP=1 < ../db/N4.6_Database_Schema.sql`

Dữ liệu thử sinh với seed cố định nên kết quả giống nhau mỗi lần. Nạp lại dữ liệu hoặc ngưỡng thì phải refresh materialized view (`load_sample.py` tự làm), nếu không API trả số cũ.

## Công cụ khác
| Lệnh | Mục đích |
|---|---|
| `uv run python scripts/export_openapi.py` | Xuất `docs/openapi.json` cho Frontend |
| `powershell -File scripts\make_bruno.ps1` | Sinh lại Bruno collection trong `bruno/` |
| `cd bruno; npx @usebruno/cli run --env local` | Chạy 11 request mẫu có kiểm tra (cần server chạy) |
| `uv run python scripts/bench_api.py 200` | Đo thời gian phản hồi baseline (cần server chạy) |

`evidence/`: ảnh và log minh chứng do `scripts/make_evidence.py` tạo; chỉ giữ trên máy, không commit.
