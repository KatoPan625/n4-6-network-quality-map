# N4.6 – Hợp đồng API (bản nháp v0.1)

- Người soạn: An (Backend) · Ngày: 10/11/2026
- Cập nhật: 10/11/2026 (thêm 3 API đọc, 15 test). Trạng thái: **NHÁP**, gửi Đạt (schema) và Đức (Frontend) góp ý trước buổi thống nhất tuần 3.
- Swagger sống: chạy backend rồi mở `http://localhost:8000/docs`.

## 1. Quy ước chung

| Quy ước | Nội dung |
|---|---|
| Tiền tố | `/api/v1/...` (riêng `/health` không có tiền tố) |
| Định dạng | JSON UTF-8; bản đồ dùng GeoJSON, hệ tọa độ WGS84 (EPSG:4326) |
| Mã vùng | `region_code` dạng chuỗi (vd `R-0-0`, sau này là mã huyện/ô lưới) |
| Thời gian | Ngày ISO 8601 `YYYY-MM-DD`; kỳ gồm `period_type` (`day`/`week`/`month`) + `period_start` |
| KPI | Đọc danh sách từ `/api/v1/kpis`, **không hard-code** ở Frontend |
| Thiếu dữ liệu | `value: null` + `status: "missing"`. Giá trị 0 là dữ liệu thật, khác với thiếu |
| Dữ liệu sai | `value: null` + `status: "invalid"` |
| Bảo mật | Không trả tọa độ trạm, vị trí thuê bao; chỉ vùng tổng hợp |
| Lỗi | HTTP status + `{"detail": "..."}` (mặc định FastAPI); xem mục 4 |

## 2. Endpoint

| # | Method + Path | Mục đích | Trạng thái |
|---|---|---|---|
| 1 | `GET /health` | Backend sống | ✅ Đã có |
| 2 | `GET /health/db` | Kết nối CSDL + phiên bản PostGIS | ✅ Đã có |
| 3 | `GET /api/v1/kpis` | Metadata KPI: tên, đơn vị, cách tính | ✅ Đã có |
| 4 | `GET /api/v1/regions` | Ranh giới vùng (GeoJSON) | ✅ Đã có |
| 5 | `GET /api/v1/kpi-values` | Giá trị KPI theo vùng/kỳ (tô màu bản đồ) | ✅ Đã có (dữ liệu thử) |
| 6 | `GET /api/v1/regions/{code}/kpis` | Chi tiết KPI 1 vùng theo thời gian | ✅ Đã có (dữ liệu thử) |
| 7 | `GET /api/v1/compare` | So sánh 2 kỳ | ✅ Đã có sớm (dữ liệu thử) |
| 8 | `POST /api/v1/imports` | Nhập file dữ liệu | 📝 Tuần 12 |
| 9 | `GET /api/v1/exports` | Xuất báo cáo tổng hợp | 📝 Tuần 12 |

## 3. Chi tiết và JSON mẫu

### 3.1 `GET /api/v1/kpis` ✅
```json
[
  {"code": "latency_ms", "name": "Do tre (mau)", "unit": "ms",
   "description": "Cách tính chờ mentor chốt", "higher_is_better": false}
]
```
`higher_is_better` để Frontend biết đảo thang màu (độ trễ thấp = tốt, thông lượng cao = tốt).

### 3.2 `GET /api/v1/regions?simplify=0` ✅
- `simplify` (0–0.01 độ): đơn giản hóa ranh giới để giảm dung lượng. Mặc định 0.
```json
{"type": "FeatureCollection", "features": [
  {"type": "Feature", "id": "R-0-0",
   "properties": {"region_code": "R-0-0", "name": "O luoi 0-0", "level": "grid"},
   "geometry": {"type": "MultiPolygon", "coordinates": [[[[106.6, 10.7], "..."]]]}}
]}
```
Geometry luôn là `MultiPolygon` để Frontend xử lý một kiểu duy nhất.

### 3.3 `GET /api/v1/kpi-values` ✅
Tham số: `kpi` (bắt buộc), `period_type` (mặc định `month`), `period_start` (bắt buộc), `region` (tùy chọn, lặp được).
```json
{
  "kpi": {"code": "latency_ms", "unit": "ms"},
  "period": {"type": "month", "start": "2026-10-01"},
  "items": [
    {"region_code": "R-0-0", "value": 42.5, "status": "ok", "updated_at": "2026-11-01T00:00:00Z"},
    {"region_code": "R-1-1", "value": null, "status": "missing", "updated_at": "2026-11-01T00:00:00Z"}
  ]
}
```
Frontend ghép `items` với `/regions` qua `region_code` (tách hình và số liệu để không tải lại ranh giới mỗi lần đổi bộ lọc).

### 3.4 `GET /api/v1/regions/{code}/kpis` ✅
Tham số: `kpi` (tùy chọn), `from`, `to`. Trả chuỗi thời gian cho màn hình chi tiết.

### 3.5 `GET /api/v1/compare` ✅
Tham số: `kpi`, `period_type`, `period_a`, `period_b`, `region` (tùy chọn).
Mỗi vùng trả `value_a`, `value_b`, `delta`; `delta = null` nếu một trong hai kỳ thiếu dữ liệu.

### 3.6 Nhập/xuất 📝
Định dạng file nhập (CSV cột như `data/sample_kpi.csv`?) và định dạng xuất (CSV/XLSX/PDF) chờ chốt với Data/QA và mentor.

## 4. Mã lỗi

| HTTP | Khi nào |
|---|---|
| 400/422 | Tham số sai (KPI không tồn tại, ngày sai định dạng) |
| 404 | Không có vùng/KPI theo mã |
| 503 | Mất kết nối CSDL |

## 5. Câu hỏi cần thống nhất (tuần 3)

1. **Đạt:** cấu trúc 3 bảng `region`, `kpi_definition`, `kpi_value` trong `db/init/01_schema_draft.sql` có hợp với schema dự kiến không?
2. **Đức:** tách `/regions` (hình) và `/kpi-values` (số) như mục 3.3 có tiện cho Leaflet/MapLibre không? Cần thêm trường nào?
3. **Vũ:** file dữ liệu nhập dùng CSV dạng cột như `data/sample_kpi.csv` được không?
4. **Mentor:** danh sách KPI, cách tính, ngưỡng tốt/chưa tốt, mức chi tiết vùng, chu kỳ cập nhật.

## 6. Công cụ kèm theo

- `docs/openapi.json`: đặc tả máy đọc được (`uv run python scripts/export_openapi.py`).
- `bruno/`: 8 request mẫu có test, mở bằng Bruno hoặc chạy `npx @usebruno/cli run --env local` trong thư mục `bruno`.
- `scripts/bench_api.py`: đo p50/p95 ở quy mô lab, chỉ là baseline, không phải chỉ tiêu nghiệm thu.
