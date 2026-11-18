# N4.6 — Bản đồ số hiển thị chất lượng mạng theo khu vực

Dự án học kỳ doanh nghiệp UTH – VNPT NET. Người dùng Claude Code trong repo này là **An** (Lại Hồ Phước An, GitHub `KatoPan625`), phụ trách Backend & API và đồng trưởng nhóm với Đạt.

## Nhóm và tiến độ

- Đạt: trưởng nhóm, yêu cầu, schema CSDL, cầu nối với mentor. An: Backend & API, đồng trưởng nhóm, thường ra quyết định cùng cả nhóm. Đức: Frontend bản đồ. Vũ: Data/QA.
- Học kỳ 01/11/2026 – 06/03/2027. Tuần 3 (15–21/11): chốt mẫu API, schema, KPI, đơn vị, cách xử lý dữ liệu thiếu; họp chốt hợp đồng API ngày 21/11.
- Mốc tiếp theo: báo cáo tháng 28/11 (tuần 4), xong thiết kế tuần 6 (06–12/12), prototype tuần 8 (báo cáo 26/12), giữa kỳ tuần 9, phát triển và kiểm thử đến tuần 12 (báo cáo 23/01/2027).

## Quyết định đã chốt

Chi tiết, ngày và lý do ở `docs/DECISIONS.md`. Thiết kế CSDL ở `docs/SCHEMA-V2.1.md` và `db/N4.6_Database_Schema_V2.1.sql`.

- Mạng **cố định** (Internet cáp quang). Không dùng RSRP, SINR hay KPI mạng di động khác.
- 8 KPI: `download_throughput`, `upload_throughput`, `latency`, `jitter`, `packet_loss_rate`, `network_availability`, `http_ip_access_failure_ratio`, `http_dropped_sessions_ratio`.
- Lưới vuông **1 km**, khung `HCM-CENTER-NE` 15 × 11 km (165 ô, mã `G1K-<i>-<j>`). Dự phòng: lưới 500 m hoặc phường/xã.
- Chu kỳ **tuần** (thứ Hai – Chủ nhật), 26 tuần từ 04/05/2026 đến 01/11/2026. Không tổng hợp lên tháng.
- Dữ liệu **mô phỏng**, luôn gắn nhãn `simulated`; không phải số liệu của VNPT.
- Ngưỡng tốt / trung bình / kém: **chưa có số**. Mỗi ngưỡng phải dẫn căn cứ; ngưỡng nhóm tự đề xuất ghi `team_proposed`, không gọi là chuẩn hay ngưỡng VNPT.

`README.md`, `docs/REQUIREMENTS.md`, `docs/PLAN.md`, `docs/DATA.md` viết ngày 04/11 nên có chỗ đã cũ (2–4 KPI, chưa chọn công nghệ). Khi mâu thuẫn, `docs/DECISIONS.md` và `docs/SCHEMA-V2.1.md` được ưu tiên. Không tự sửa các file cũ nếu An chưa yêu cầu.

## Cấu trúc repo

```
backend/   FastAPI + PostgreSQL/PostGIS (sandbox, giữ lịch sử commit từ 10/11)
db/        SQL schema chính thức của nhóm (V2.1)
docs/      tài liệu nhóm, DECISIONS.md, SCHEMA-V2.1.md, daily/<tên>/
frontend/  chưa có (Đức)
data/      chưa có (Vũ); raw/private/generated bị .gitignore
```

## Trạng thái Backend

`backend/` vẫn chạy trên **schema nháp** `backend/db/init/01_schema_draft.sql` (3 bảng `region`, `kpi_definition`, `kpi_value`; lưới 3×3 giả lập; 2 KPI mẫu). Việc kế tiếp là chuyển sang V2.1.

API hiện có: `GET /health`, `/health/db`, `/api/v1/kpis`, `/api/v1/regions?simplify=`, `/api/v1/kpi-values?kpi=&period_start=&period_type=&region=`, `/api/v1/regions/{code}/kpis?kpi=&from=&to=`, `/api/v1/compare?kpi=&period_a=&period_b=` (delta = B − A, null nếu một bên thiếu). Dự kiến tuần 12: `POST /imports`, `GET /exports`.

Công nghệ: PostgreSQL 17 + PostGIS 3.5.2 (image `postgis/postgis:17-3.5`), SRID 4326, FastAPI, SQLAlchemy 2 (sync), GeoAlchemy2, psycopg 3, pydantic-settings, uv, pytest + httpx, ruff, Bruno.

## Lệnh (Windows PowerShell, chạy trong `backend/`)

```powershell
docker compose up -d --wait            # cần mở Docker Desktop trước
uv sync
uv run python scripts/load_sample.py   # nạp dữ liệu thử
uv run uvicorn app.main:app --reload   # http://localhost:8000/docs
uv run pytest
uv run ruff check . ; uv run ruff format .
bru run --env local                    # trong backend/bruno
```

Nạp schema V2.1: `psql -d <db> -v ON_ERROR_STOP=1 -f db/N4.6_Database_Schema_V2.1.sql`.

## Quy ước API (giữ nguyên khi sửa)

- Trao đổi bằng `region_code`, `kpi_code`, `source_code`; không trả khóa tự tăng.
- Thiếu dữ liệu: `value: null` + `status: "missing"`; không bao giờ thay bằng 0. Có thêm `"invalid"`.
- Danh sách KPI đọc từ CSDL, không viết cứng.
- Geometry luôn MultiPolygon (bọc `ST_Multi` sau `ST_SimplifyPreserveTopology`).
- Lỗi trả `{"detail": ...}`. CORS chỉ cho GET từ `http://localhost:5173`.
- Không lưu, không trả tọa độ trạm hay thuê bao; chỉ dữ liệu tổng hợp theo ô.
- Từ V2.1: phản hồi có `data_nature` (để hiện nhãn "Dữ liệu mô phỏng") và `quality_level`; tham số `source`, mặc định là nguồn có `is_default`.

## Lỗi đã gặp

- Docker Desktop chưa chạy thì `docker compose` báo lỗi kết nối. Mở Docker Desktop rồi chạy lại; nếu volume bị xóa thì nạp lại dữ liệu mẫu.
- Docker Compose đặt tên project theo thư mục, nên chạy từ `backend/` của repo này tạo volume mới, khác sandbox cũ ở `D:\University\HKDN\n46-backend-sandbox`. Phải nạp lại dữ liệu.
- `Set-Content -Encoding utf8` của PowerShell 5 thêm BOM, làm Bruno lỗi "Unexpected token". Ghi UTF-8 không BOM.
- Console Windows làm vỡ dấu tiếng Việt khi in log; ghi log ra file UTF-8 nếu cần làm minh chứng.
- TP.HCM bỏ cấp quận từ 01/07/2025 (168 đơn vị cấp xã). Không viết "Quận 1", "Quận 2".
- QCVN 34:2019/BTTTT đã bị thay bằng **QCVN 34:2022/BTTTT**.

## Quy tắc làm việc với An

- Trả lời bằng tiếng Việt, ngắn, đi thẳng vào việc; gọi là "An"; chỉ ra lỗi trực tiếp, kể cả lỗi của An.
- **Hỏi trước** khi sửa file ngoài phạm vi yêu cầu, trước khi commit, push, gửi tin nhắn hay email.
- Không push thẳng `main`. Đặt nhánh theo `CONTRIBUTING.md` (ví dụ `feat/25-bo-loc`), mở PR để người khác review.
- Không commit `.env`, token, dữ liệu raw/private/generated.
- Chạy `pytest` và `ruff` trước khi báo xong; không nói "đã xong" khi chưa có kết quả chạy.
- Daily report: mỗi ngày một file `docs/daily/An/YYYY-MM-DD_DailyReport_An.md` theo `docs/REPORT-TEMPLATE.md`, kèm minh chứng (commit, PR, ảnh trong `backend/evidence/`).

## Việc đang mở (cập nhật 18/11/2026)

1. Backend chuyển sang schema V2.1: API đọc `v_kpi_values_classified`, thêm `data_nature`, `quality_level`, `source`; cập nhật test, dữ liệu mẫu, `backend/docs/api-contract.md`. Hạn 20/11.
2. Vũ viết script sinh dữ liệu mô phỏng 165 ô × 8 KPI × 26 tuần (~34.000 dòng) và điền phương pháp, giả định vào nguồn `SIM-V1`.
3. An và Vũ tra ngưỡng 3 mức (QCVN 34:2022/BTTTT; ITU-T Y.1540), nạp `kpi_thresholds`, chạy `SELECT * FROM v_kpi_threshold_check;`.
4. Gửi Đức `api-contract.md`, `openapi.json`, JSON mẫu; Đức chọn Leaflet hay MapLibre.
5. Đạt gửi thầy email xác nhận hướng đã chốt.
6. Mời thành viên vào repo; bật bảo vệ nhánh `main`.
7. Lưu ảnh email thầy ngày 17/11 vào `docs/mentor/`.
8. Đối chiếu số bảng, số mục ETSI TS 103 222-2 trước khi trích vào báo cáo.
