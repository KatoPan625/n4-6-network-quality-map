# N4.6 – Backend

Bản thử của phần Backend/API (FastAPI + PostgreSQL/PostGIS) cho đề tài
"Xây dựng bản đồ số hiển thị chất lượng mạng theo khu vực". Lịch sử commit giữ từ sandbox ngày 10/11.
CSDL dùng schema chính thức V2.1 của nhóm (`../db/N4.6_Database_Schema_V2.1.sql`); dữ liệu trong `data/` là dữ liệu thử của Backend (nguồn `BE-SAMPLE`), không phải bộ mô phỏng `SIM-V1`.

## Yêu cầu
Docker Desktop (đang chạy), [uv](https://docs.astral.sh/uv/), Python 3.13.

## Chạy lần đầu
```powershell
copy .env.example .env          # rồi đổi DB_PASSWORD
docker compose up -d --wait     # tạo CSDL + schema V2.1 (165 ô, 8 KPI, nguồn SIM-V1)
uv sync
uv run python scripts/load_sample.py   # nạp dữ liệu thử BE-SAMPLE (CSV có sẵn trong data/)
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
| `../db/` | Schema V2.1, Docker nạp khi tạo CSDL lần đầu |
| `scripts/` | Tạo và nạp dữ liệu thử |
| `data/` | KPI thử 165 ô × 8 KPI × 2 tuần, nguồn `BE-SAMPLE` (không phải dữ liệu thật) |
| `docs/api-contract.md` | Hợp đồng API bản nháp |
| `tests/` | Test API (cần CSDL đang chạy) |

## Làm lại CSDL từ đầu
Schema chỉ chạy khi volume trống: `docker compose down -v` (xóa toàn bộ dữ liệu trong CSDL local) rồi chạy lại các bước trên.

Sinh lại file dữ liệu thử: `uv run python scripts/make_sample_data.py` (seed cố định, kết quả giống nhau mỗi lần).

## Công cụ khác
| Lệnh | Mục đích |
|---|---|
| `uv run python scripts/export_openapi.py` | Xuất `docs/openapi.json` cho Frontend |
| `powershell -File scripts\make_bruno.ps1` | Sinh lại Bruno collection trong `bruno/` |
| `cd bruno; npx @usebruno/cli run --env local` | Chạy 8 request mẫu có kiểm tra (cần server chạy) |
| `uv run python scripts/bench_api.py 200` | Đo thời gian phản hồi baseline (cần server chạy) |

`evidence/`: ảnh và log minh chứng do `scripts/make_evidence.py` tạo; chỉ giữ trên máy, không commit.
