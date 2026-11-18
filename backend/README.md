# N4.6 – Backend sandbox

Bản thử của phần Backend/API (FastAPI + PostgreSQL/PostGIS) cho đề tài
"Xây dựng bản đồ số hiển thị chất lượng mạng theo khu vực". **Chưa phải repo chung**;
schema trong `db/init/` là bản nháp, dữ liệu trong `data/` là dữ liệu thử giả lập.

## Yêu cầu
Docker Desktop (đang chạy), [uv](https://docs.astral.sh/uv/), Python 3.13.

## Chạy lần đầu
```powershell
copy .env.example .env          # rồi đổi DB_PASSWORD
docker compose up -d --wait     # tạo CSDL + schema nháp
uv sync
uv run python scripts/make_sample_data.py
uv run python scripts/load_sample.py
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
| `db/init/` | SQL chạy khi tạo CSDL lần đầu |
| `scripts/` | Tạo và nạp dữ liệu thử |
| `data/` | Lưới 3×3 giả lập + KPI giả (không phải dữ liệu thật) |
| `docs/api-contract.md` | Hợp đồng API bản nháp |
| `tests/` | Test API (cần CSDL đang chạy) |

## Làm lại CSDL từ đầu
Schema chỉ chạy khi volume trống: `docker compose down -v` rồi chạy lại các bước trên.

## Công cụ khác
| Lệnh | Mục đích |
|---|---|
| `uv run python scripts/export_openapi.py` | Xuất `docs/openapi.json` cho Frontend |
| `powershell -File scripts\make_bruno.ps1` | Sinh lại Bruno collection trong `bruno/` |
| `cd bruno; npx @usebruno/cli run --env local` | Chạy 8 request mẫu có kiểm tra (cần server chạy) |
| `uv run python scripts/bench_api.py 200` | Đo thời gian phản hồi baseline (cần server chạy) |

`evidence/`: ảnh và log minh chứng theo ngày cho báo cáo.
