# N4.6 – Hợp đồng API (bản nháp)

- Người soạn: An (Backend). Cập nhật: 19/11/2026. Trạng thái: **NHÁP**, chốt ở buổi họp 21/11.
- Dựa trên schema `db/N4.6_Database_Schema.sql` (thiết kế: `docs/SCHEMA.md`): mạng di động 4G, KPI theo cell, tổng hợp lên tỉnh/phường, theo giờ/ngày.
- Swagger: chạy backend rồi mở `http://localhost:8000/docs`. Đặc tả máy đọc: `docs/openapi.json`.

## 1. Quy ước chung

| Quy ước | Nội dung |
|---|---|
| Tiền tố | `/api/v1/...` (riêng `/health` không có tiền tố) |
| Định dạng | JSON UTF-8; bản đồ dùng GeoJSON WGS84 (EPSG:4326), geometry luôn `MultiPolygon` |
| Mã trao đổi | `region_code`, `kpi_code`, `source_code`. Không trả khóa tự tăng, không trả mã cell hay tọa độ trạm |
| Thời gian | Giờ Việt Nam. Mọi mốc thời gian trả về dạng `+07:00`. `at` theo giờ: `YYYY-MM-DDTHH:00` (không cần múi giờ; có thể kèm `+07:00` hoặc `Z`); theo ngày: `YYYY-MM-DD` |
| Khoảng dữ liệu | Lấy từ `/api/v1/sources` (`period_from` gồm, `period_to` không gồm). `at` ngoài khoảng trả 422 |
| KPI | Đọc danh sách từ `/api/v1/kpis`, **không viết cứng** ở Frontend |
| Nguồn | Tham số `source`. Bỏ trống thì dùng nguồn `is_default` (`SIM-4G-2026-10`, bộ mô phỏng của Vũ). Dữ liệu thử của Backend là `BE-SAMPLE` (72 giờ từ 01/10/2026) |
| Nhãn mô phỏng | `source.data_nature = "simulated"` thì Frontend hiện nhãn **"Dữ liệu mô phỏng"** |
| Thiếu dữ liệu | `value: null`; không bao giờ thay bằng 0. 0 là số đo thật (ví dụ traffic = 0) |
| CORS | Chỉ `GET` từ `http://localhost:5173` |

### Trạng thái một vùng

| Trường | Ý nghĩa | Frontend hiển thị |
|---|---|---|
| `status: "ok"` | Mọi cell của vùng đều báo cáo KPI đó | Tô màu theo `quality_level` |
| `status: "partial"` | Thiếu một phần cell (theo ngày: thiếu một phần cell-giờ) | Vẫn tô màu theo `quality_level`, thêm viền nét đứt hoặc biểu tượng cảnh báo và "x/y cell" |
| `status: "missing"` | Không cell nào báo cáo | Màu xám, `value: null` |
| `reason: "no_positive_traffic"` | Có báo cáo nhưng tổng traffic dương bằng 0 nên không tính được trung bình có trọng số; `value: null` | Màu xám, chú thích "không có lưu lượng" |
| `quality_level` | `good`/`medium`/`poor`; `null` khi chưa có ngưỡng hoặc `value` null | Thang màu; đảo chiều theo `higher_is_better` |
| `threshold_type` | `standard` hoặc `team_proposed` (ngưỡng nhóm đề xuất, không phải chuẩn) | Ghi trong chú giải |

## 2. Endpoint

| # | Method + Path | Mục đích |
|---|---|---|
| 1 | `GET /health`, `GET /health/db` | Backend và CSDL còn sống |
| 2 | `GET /api/v1/kpis` | Danh mục 4 KPI kèm đơn vị, cách tính, cách tổng hợp |
| 3 | `GET /api/v1/sources` | Nguồn dữ liệu và khoảng thời gian có dữ liệu |
| 4 | `GET /api/v1/regions?level=province\|ward&simplify=` | Ranh giới GeoJSON |
| 5 | `GET /api/v1/kpi-values` | Giá trị 1 KPI của mọi vùng ở 1 giờ hoặc 1 ngày (tô màu bản đồ) |
| 6 | `GET /api/v1/regions/{code}/kpis` | Chuỗi thời gian KPI của 1 vùng (màn hình chi tiết) |
| 7 | `GET /api/v1/compare` | So sánh 1 KPI giữa 2 mốc |
| 8 | `POST /api/v1/imports`, `GET /api/v1/exports` | 📝 Tuần 12 |

## 3. Chi tiết và JSON mẫu

JSON mẫu lấy từ nguồn thử `BE-SAMPLE` (giá trị giả lập, chỉ để test).

### 3.1 `GET /api/v1/kpis`
```json
[{"kpi_code": "cssr", "kpi_name": "Call Setup Success Rate (CSSR / A1)", "kpi_group": "accessibility",
  "unit": "%", "higher_is_better": true, "is_quality_kpi": true, "is_ratio": true,
  "aggregation_rule": "traffic_weighted", "valid_min": 0.0, "valid_max": 100.0, "display_order": 1,
  "description": "...", "calculation_method": "...", "reference_name": "3GPP TS 32.450 V19.0.0 ..."}]
```
`traffic` có `higher_is_better: null`, `aggregation_rule: "sum"` và không có ngưỡng; Frontend tô theo thang liên tục.

### 3.2 `GET /api/v1/sources`
```json
[{"source_code": "SIM-4G-2026-10", "source_name": "...", "data_nature": "simulated",
  "period_from": "2026-10-01T00:00:00+07:00", "period_to": "2026-10-31T00:00:00+07:00", "is_default": true}]
```

### 3.3 `GET /api/v1/regions`
- `level`: `province` (mặc định, 34 vùng) hoặc `ward` (168 phường/xã TP.HCM).
- `simplify`: 0–0.01 độ, mặc định 0.001 (khoảng 100 m). Khoảng 425 KB cho tỉnh, 167 KB cho phường; khi client gửi `Accept-Encoding: gzip` (trình duyệt tự gửi), API nén còn khoảng 126 KB và 38 KB.
```json
{"type": "FeatureCollection", "features": [
  {"type": "Feature", "id": "79",
   "properties": {"region_code": "79", "region_name": "Thành phố Hồ Chí Minh", "region_level": "province", "parent_code": null},
   "geometry": {"type": "MultiPolygon", "coordinates": ["..."]}}]}
```
Phường có `parent_code: "79"`. Nguồn ranh giới: sapnhap.bando.com.vn (Bộ NN&MT), bản trích xuất `myleo198/sapnhap-bando-vn`, CC BY-NC 4.0. Frontend phải ghi attribution.

### 3.4 `GET /api/v1/kpi-values`
Tham số: `kpi` (bắt buộc), `at` (bắt buộc), `level` (`province` mặc định), `period_type` (`hour` mặc định), `region` (lặp được), `source`.

Ví dụ: `/api/v1/kpi-values?kpi=cssr&level=ward&at=2026-10-02T20:00&source=BE-SAMPLE&region=25747&region=25750`
```json
{
  "kpi": {"kpi_code": "cssr", "kpi_name": "Call Setup Success Rate (CSSR / A1)", "unit": "%",
          "higher_is_better": true, "aggregation_rule": "traffic_weighted"},
  "source": {"source_code": "BE-SAMPLE", "source_name": "Du lieu thu cua Backend", "data_nature": "simulated",
             "period_from": "2026-10-01T00:00:00+07:00", "period_to": "2026-10-04T00:00:00+07:00"},
  "level": "ward",
  "period": {"type": "hour", "at": "2026-10-02T20:00:00+07:00"},
  "items": [
    {"region_code": "25747", "region_name": "Phường Thủ Dầu Một", "value": 97.9275, "status": "partial",
     "quality_level": null, "threshold_type": null, "cells_reported": 1, "cells_total": 2,
     "updated_at": "2026-11-19T10:54:42+07:00", "reason": null},
    {"region_code": "25750", "region_name": "Phường Phú Lợi", "value": null, "status": "ok",
     "quality_level": null, "threshold_type": null, "cells_reported": 2, "cells_total": 2,
     "updated_at": "2026-11-19T10:54:42+07:00", "reason": "no_positive_traffic"}
  ]
}
```
- Mọi vùng của cấp đó đều có trong `items`.
- `period_type=day` (`at=2026-10-02`) thêm `cell_hours_reported`, `cell_hours_expected`; `status` theo ngày tính trên số cell-giờ.
- `quality_level` đang `null` vì bảng ngưỡng chưa có số; khi nạp ngưỡng và refresh, API tự trả mà không sửa code.
- Frontend ghép `items` với `/regions` qua `region_code`, không tải lại ranh giới mỗi lần đổi bộ lọc.

### 3.5 `GET /api/v1/regions/{code}/kpis`
Tham số: `kpi`, `period_type` (`day` mặc định), `from`, `to` (cùng định dạng với `at`), `source`. Bỏ trống `from`/`to` thì lấy cả khoảng của nguồn.
```json
{"region_code": "25760", "region_name": "Phường Bình Dương", "region_level": "ward", "parent_code": "79",
 "source": {"...": "..."}, "period_type": "day",
 "kpis": [{"kpi_code": "cssr", "kpi_name": "...", "unit": "%", "series": [
   {"at": "2026-10-01", "value": 93.52, "status": "ok", "quality_level": null, "threshold_type": null,
    "cells_reported": 2, "cells_total": 2, "cell_hours_reported": 48, "cell_hours_expected": 48,
    "updated_at": "...", "reason": null}]}]}
```
`kpis` theo `display_order`; `series` có đủ mọi mốc trong khoảng (mốc thiếu dữ liệu vẫn có, với `value: null`).

### 3.6 `GET /api/v1/compare`
Tham số: `kpi`, `a`, `b` (cùng định dạng với `at`), `level`, `period_type` (`day` mặc định), `region`, `source`.
Mỗi vùng trả `value_a`, `status_a`, `quality_level_a`, `value_b`, `status_b`, `quality_level_b`, `delta`.
`delta = value_b − value_a`, làm tròn 4 chữ số; `null` nếu một trong hai mốc không có giá trị.

## 4. Mã lỗi

| HTTP | Khi nào |
|---|---|
| 404 | Không có KPI, vùng hoặc nguồn theo mã; chưa có nguồn mặc định |
| 422 | Thiếu tham số; `at`/`from`/`to` sai định dạng, không đúng đầu giờ, hoặc ngoài khoảng dữ liệu của nguồn; `from > to`; `level`/`period_type` không hợp lệ |
| 503 | Mất kết nối CSDL (`/health/db`) |

## 5. Hiệu năng (đo 19/11/2026, máy local, 1 client, `scripts/bench_api.py`)

| Endpoint | p50 | p95 |
|---|---:|---:|
| `/regions` (34 tỉnh) | 139 ms | 172 ms |
| `/regions?level=ward` | 176 ms | 199 ms |
| `/kpi-values` (giờ, 168 phường) | 9 ms | 10 ms |
| `/regions/79/kpis` (72 giờ × 4 KPI) | 11 ms | 12 ms |
| `/compare` (ngày, 34 tỉnh) | 7 ms | 8 ms |

API đọc 2 materialized view `mv_region_kpi`, `mv_region_kpi_daily`. Sau mỗi lần nạp dữ liệu hoặc ngưỡng phải chạy `db/N4.6_Refresh_Materialized_Views.sql`, nếu không API trả số cũ.

## 6. Câu hỏi cần thống nhất ngày 21/11

1. **Đức:** cách hiển thị `partial` (tô màu kèm viền nét đứt) và `reason: "no_positive_traffic"` có ổn không? Ranh giới nặng khoảng 425 KB; có cần `simplify` lớn hơn không?
2. **Đức:** bản đồ tỉnh bấm vào TP.HCM thì gọi `/regions?level=ward` và `/kpi-values?level=ward`. Có cần endpoint khác không?
3. **Vũ:** sinh dữ liệu `SIM-4G-2026-10` trực tiếp vào `cell_kpi_values` (mỗi cell × KPI × giờ một dòng), mã cell không lộ vị trí; xem `scripts/load_sample.py` làm mẫu.
4. **Cả nhóm:** số ngưỡng tốt/trung bình/kém cho 3 KPI chất lượng (`team_proposed`).

## 7. Công cụ kèm theo

- Nạp dữ liệu: `uv run python scripts/load_regions.py` (ranh giới) rồi `uv run python scripts/load_sample.py` (BE-SAMPLE và refresh MV).
- `bruno/`: 11 request mẫu có test, chạy `npx @usebruno/cli run --env local` trong thư mục `bruno`.
- `scripts/bench_api.py`: đo p50/p95 ở quy mô lab, chỉ là baseline.
