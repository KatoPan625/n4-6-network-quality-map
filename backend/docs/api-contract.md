# N4.6 – Hợp đồng API (bản nháp v0.2)

- Người soạn: An (Backend). Bản v0.1: 10/11/2026. Bản v0.2: 18/11/2026.
- v0.2 chuyển sang schema V2.1 (`db/N4.6_Database_Schema_V2.1.sql`, `docs/SCHEMA-V2.1.md`). Trạng thái: **NHÁP**, chốt ở buổi họp 21/11.
- Swagger: chạy backend rồi mở `http://localhost:8000/docs`. Đặc tả máy đọc: `docs/openapi.json`.

## Thay đổi so với v0.1

| Mục | v0.1 | v0.2 |
|---|---|---|
| Vùng | Lưới thử 3×3, mã `R-0-0` | Lưới 1 km, 165 ô khung `HCM-CENTER-NE`, mã `G1K-<i>-<j>` |
| KPI | 2 KPI mẫu (`latency_ms`, `packet_loss_pct`) | 8 KPI mạng cố định, đọc từ bảng `kpis` |
| Chu kỳ | `day`/`week`/`month`, mặc định `month` | Chỉ `week`; `period_start` phải là thứ Hai |
| Khóa KPI | `code`, `name` | `kpi_code`, `kpi_name` |
| Thuộc tính ô | `name`, `level` | `region_name`, `region_level` |
| Nguồn | Không có | Tham số `source`; mọi phản hồi giá trị có khối `source` kèm `data_nature` |
| Mức chất lượng | Không có | Mỗi giá trị có `quality_level` và `threshold_type` |
| `updated_at` | Có trong từng giá trị | Bỏ (view không có cột này) |

## 1. Quy ước chung

| Quy ước | Nội dung |
|---|---|
| Tiền tố | `/api/v1/...` (riêng `/health` không có tiền tố) |
| Định dạng | JSON UTF-8; bản đồ dùng GeoJSON WGS84 (EPSG:4326) |
| Mã trao đổi | `region_code`, `kpi_code`, `source_code`. Không trả khóa tự tăng |
| Thời gian | Ngày ISO `YYYY-MM-DD`. Một kỳ là một tuần thứ Hai – Chủ nhật, xác định bằng `period_start` (thứ Hai). Kỳ dữ liệu: 04/05/2026 – 01/11/2026 (26 tuần) |
| KPI | Đọc danh sách từ `/api/v1/kpis`, **không viết cứng** ở Frontend |
| Nguồn dữ liệu | Tham số `source` (mã nguồn). Bỏ trống thì dùng nguồn `is_default` (hiện là `SIM-V1`) |
| Nhãn mô phỏng | `source.data_nature = "simulated"` thì Frontend hiện nhãn **"Dữ liệu mô phỏng"** |
| Thiếu dữ liệu | `value: null` + `status: "missing"`. Giá trị 0 là số đo thật, khác với thiếu |
| Dữ liệu sai | `value: null` + `status: "invalid"` |
| Mức chất lượng | `quality_level`: `good` / `medium` / `poor`, hoặc `null` khi chưa có ngưỡng hay `status` khác `ok`. `threshold_type`: `standard` hoặc `team_proposed` (ngưỡng nhóm tự đề xuất, không phải chuẩn) |
| Bảo mật | Không trả tọa độ trạm, vị trí thuê bao; chỉ số liệu tổng hợp theo ô |
| Lỗi | HTTP status + `{"detail": "..."}`; xem mục 4 |
| CORS | Chỉ `GET` từ `http://localhost:5173` |

## 2. Endpoint

| # | Method + Path | Mục đích | Trạng thái |
|---|---|---|---|
| 1 | `GET /health` | Backend sống | ✅ |
| 2 | `GET /health/db` | Kết nối CSDL + phiên bản PostGIS | ✅ |
| 3 | `GET /api/v1/kpis` | Danh mục KPI | ✅ V2.1 |
| 4 | `GET /api/v1/regions` | Ranh giới ô lưới (GeoJSON) | ✅ V2.1 |
| 5 | `GET /api/v1/kpi-values` | Giá trị 1 KPI của mọi ô trong 1 tuần (tô màu bản đồ) | ✅ V2.1 |
| 6 | `GET /api/v1/regions/{code}/kpis` | Chuỗi thời gian KPI của 1 ô | ✅ V2.1 |
| 7 | `GET /api/v1/compare` | So sánh 2 tuần | ✅ V2.1 |
| 8 | `POST /api/v1/imports` | Nhập file dữ liệu | 📝 Tuần 12 |
| 9 | `GET /api/v1/exports` | Xuất báo cáo tổng hợp | 📝 Tuần 12 |

## 3. Chi tiết và JSON mẫu

JSON mẫu dưới đây lấy từ nguồn thử `BE-SAMPLE` của Backend (giá trị ngẫu nhiên, chỉ để test).

### 3.1 `GET /api/v1/kpis`
Trả 8 KPI đang dùng, theo `display_order`.
```json
[
  {"kpi_code": "latency", "kpi_name": "Latency (RTT)", "kpi_group": "internet_performance",
   "unit": "ms", "higher_is_better": false, "is_ratio": false, "valid_min": 0.0, "valid_max": null,
   "description": "...", "calculation_method": "...", "aggregation_method": "Trung vi cac phep do hop le trong tuan.",
   "reference_name": "ITU-T Y.1540 (IPTD)", "display_order": 3}
]
```
`higher_is_better` để Frontend biết đảo thang màu (độ trễ thấp là tốt, thông lượng cao là tốt).

### 3.2 `GET /api/v1/regions?simplify=0`
- `simplify` (0–0.01 độ): đơn giản hóa ranh giới. Mặc định 0. Ô lưới vuông nên thường không cần.
```json
{"type": "FeatureCollection", "features": [
  {"type": "Feature", "id": "G1K-683-1190",
   "properties": {"region_code": "G1K-683-1190", "region_name": "O 683-1190", "region_level": "grid_1km"},
   "geometry": {"type": "MultiPolygon", "coordinates": [[[[106.69, 10.76], "..."]]]}}
]}
```
Geometry luôn là `MultiPolygon`.

### 3.3 `GET /api/v1/kpi-values`
Tham số: `kpi` (bắt buộc), `period_start` (bắt buộc, thứ Hai), `period_type` (chỉ `week`, mặc định `week`), `region` (tùy chọn, lặp được), `source` (tùy chọn).

Ví dụ: `/api/v1/kpi-values?kpi=packet_loss_rate&period_start=2026-10-19&source=BE-SAMPLE&region=G1K-684-1190&region=G1K-697-1200`
```json
{
  "kpi": {"kpi_code": "packet_loss_rate", "unit": "%", "higher_is_better": false},
  "source": {"source_code": "BE-SAMPLE", "source_name": "Du lieu thu cua Backend", "data_nature": "simulated"},
  "period": {"type": "week", "start": "2026-10-19"},
  "items": [
    {"region_code": "G1K-684-1190", "value": 1.214629, "status": "ok", "sample_count": 133,
     "quality_level": null, "threshold_type": null},
    {"region_code": "G1K-697-1200", "value": null, "status": "invalid", "sample_count": 66,
     "quality_level": null, "threshold_type": null}
  ]
}
```
- Mọi ô đều có mặt trong `items`. Ô không có dòng dữ liệu trả `value: null`, `status: "missing"`, `sample_count: 0`.
- `quality_level` đang `null` vì bảng `kpi_thresholds` chưa có số ngưỡng (An và Vũ đang tra). Khi nạp ngưỡng, API tự trả mức mà không cần sửa code.
- Frontend ghép `items` với `/regions` qua `region_code`, để không tải lại ranh giới mỗi lần đổi bộ lọc.

### 3.4 `GET /api/v1/regions/{code}/kpis`
Tham số: `kpi`, `from`, `to`, `period_type`, `source` (đều tùy chọn).
```json
{
  "region_code": "G1K-690-1195",
  "source": {"source_code": "BE-SAMPLE", "source_name": "...", "data_nature": "simulated"},
  "period_type": "week",
  "kpis": [
    {"kpi_code": "latency", "kpi_name": "Latency (RTT)", "unit": "ms", "series": [
      {"period_start": "2026-10-19", "value": 44.6, "status": "ok", "sample_count": 72,
       "quality_level": null, "threshold_type": null},
      {"period_start": "2026-10-26", "value": null, "status": "missing", "sample_count": 0,
       "quality_level": null, "threshold_type": null}
    ]}
  ]
}
```
`series` chỉ có các tuần có dòng trong CSDL; tuần không có dòng nào không xuất hiện.

### 3.5 `GET /api/v1/compare`
Tham số: `kpi`, `period_a`, `period_b` (đều là thứ Hai), `period_type`, `region`, `source`.
Mỗi ô trả `value_a`, `status_a`, `quality_level_a`, `value_b`, `status_b`, `quality_level_b`, `delta`.
`delta = value_b − value_a`, làm tròn 4 chữ số; `null` nếu một trong hai tuần thiếu dữ liệu.

### 3.6 Nhập/xuất 📝
File nhập dự kiến theo cột của `data/sample_kpi.csv`: `source_code, region_code, kpi_code, period_start, value, status, sample_count, numerator_value, denominator_value, quality_note`. KPI tỉ lệ (`%`) bắt buộc có tử số, mẫu số và `value = tử / mẫu × 100`; CSDL kiểm bằng trigger. Định dạng xuất chờ chốt với Vũ và mentor.

## 4. Mã lỗi

| HTTP | Khi nào |
|---|---|
| 404 | Không có KPI, ô hoặc nguồn theo mã; chưa có nguồn mặc định |
| 422 | Sai định dạng ngày, `period_type` khác `week`, ngày không phải thứ Hai, `from > to` |
| 503 | Mất kết nối CSDL (`/health/db`) |

## 5. Câu hỏi cần thống nhất ngày 21/11

1. **Đức:** dùng khối `source.data_nature` để hiện nhãn "Dữ liệu mô phỏng" và `quality_level` + `threshold_type` cho chú giải có ổn không? Có cần endpoint `GET /api/v1/sources` để chọn nguồn không?
2. **Đức:** đổi khóa `code` → `kpi_code`, `name` → `kpi_name`/`region_name` có ảnh hưởng gì không? Hiện Frontend chưa dùng nên đổi lúc này không tốn công.
3. **Vũ:** file nhập theo cột ở mục 3.6 có tiện cho script sinh dữ liệu `SIM-V1` không?
4. **Đạt:** duyệt schema V2.1 trong PR để Backend giữ nguyên file SQL chung.

## 6. Công cụ kèm theo

- Dữ liệu thử: `uv run python scripts/make_sample_data.py` rồi `uv run python scripts/load_sample.py`. Nạp vào nguồn riêng `BE-SAMPLE` (`is_default = FALSE`), không đụng `SIM-V1`.
- `bruno/`: 8 request mẫu có test, chạy `npx @usebruno/cli run --env local` trong thư mục `bruno`.
- `scripts/bench_api.py`: đo p50/p95 ở quy mô lab, chỉ là baseline.
