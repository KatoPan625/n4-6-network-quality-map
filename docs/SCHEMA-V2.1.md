**DATABASE SCHEMA**

**V2.1 — MẠNG CỐ ĐỊNH | GRID 1 KM | DỮ LIỆU MÔ PHỎNG**

Đề tài N4.6 — Xây dựng bản đồ số hiển thị chất lượng mạng theo khu vực

| **Thông số đã chốt** | **Giá trị** |
|----|----|
| Loại mạng nghiên cứu | Mạng cố định — Internet cáp quang (FTTH) |
| Bản chất dữ liệu | Dữ liệu mô phỏng; gắn nhãn `simulated`, không đại diện số liệu đo của VNPT |
| Phạm vi nghiên cứu | Khung 15 km × 11 km từ khu Bến Thành mở rộng về phía Thủ Đức cũ (mục 2.1) |
| Đơn vị không gian | Lưới vuông 1 km × 1 km, 165 ô, ô nguyên vẹn (không cắt biên) |
| Chu kỳ dữ liệu | Theo tuần, thứ Hai đến Chủ nhật; không tổng hợp lên tháng |
| Khoảng thời gian mô phỏng | 26 tuần: 04/05/2026 – 01/11/2026 |
| Công nghệ CSDL | PostgreSQL 17 + PostGIS 3.5.2 |
| Mô hình dữ liệu | 6 bảng: study_areas, regions, kpis, kpi_thresholds, data_sources, kpi_values; 2 view |

Trạng thái: V2.1 sửa các lỗi của V2 và đã chạy thử toàn bộ file SQL (tạo bảng, sinh lưới, nạp mẫu, 14 trường hợp dữ liệu sai đều bị chặn). Ngưỡng số cho 3 mức chất lượng vẫn để trống, chờ tra cứu căn cứ.

*Mục đích: bàn giao cho Backend / Data / Frontend thống nhất cấu trúc dữ liệu và triển khai.*

# 0. Thay đổi so với V2

| # | Vấn đề trong V2 | Cách xử lý trong V2.1 |
|----|----|----|
| 1 | Phạm vi nghiên cứu chưa xác định nên không sinh được bảng `regions`; số ô có thể từ ~150 đến ~6.800 | Thêm bảng `study_areas`, chốt khung 15 × 11 km = 165 ô, ~34.000 dòng `kpi_values` cho 26 tuần |
| 2 | Quy tắc "thiếu dữ liệu thì value = NULL" chỉ ghi bằng lời | CHECK: `ok` bắt buộc có `value` và `sample_count > 0`; `missing`/`invalid` bắt buộc `value` NULL; `invalid` bắt buộc có `quality_note` |
| 3 | Ngưỡng không có quy ước biên, kiểm tra chồng lấn giao cho "logic ứng dụng" | Quy ước khoảng `[min, max)`; CSDL tự chặn chồng lấn bằng EXCLUDE; view `v_kpi_threshold_check` báo thiếu mức, hở hoặc sai chiều |
| 4 | Giá trị tuần của 4 KPI là trung vị nên không gộp lên tháng được | Chỉ dùng chu kỳ tuần; bỏ hẳn tổng hợp tháng khỏi phạm vi |
| 5 | `region_level` chỉ nhận `grid_1km`, bỏ `parent_region_id`; mất đường lui sang phường/xã hoặc lưới 500 m | `region_level` nhận `grid_1km`, `grid_500m`, `ward`; giữ `parent_region_id`; `grid_col/row` bắt buộc khi là lưới |
| 6 | Cho phép cắt ô biên; ô nhỏ hơn 1 km² so sánh không công bằng | Giữ ô vuông nguyên vẹn; khung căn theo bội số 1.000 m nên mọi ô đúng 1 km² |
| 7 | Chưa nói cách lấy mã ô ổn định | `grid_col`, `grid_row` = `i`, `j` của `ST_SquareGrid(1000, …)` trong EPSG:32648, gốc mặc định (0,0) |
| 8 | Chưa có ngày bắt đầu và kết thúc kỳ mô phỏng | 04/05/2026 (thứ Hai) – 01/11/2026 (Chủ nhật), lưu trong `data_sources`; trigger chặn tuần nằm ngoài khoảng |
| 9 | Không kiểm `value` khớp tử số/mẫu số; miền 0–100% chỉ là ghi chú | Trigger kiểm miền giá trị theo `kpis.valid_min/valid_max` và `value = tử/mẫu × 100` với KPI tỷ lệ |
| 10 | UNIQUE không có `source_id`; không lưu được song song dữ liệu mô phỏng và dữ liệu công khai | UNIQUE (source_id, kpi_id, period_start, region_id); `data_sources.is_default` chọn nguồn API trả về mặc định |
| 11 | Thiếu quy chuẩn Việt Nam; link ITU-T E.812 là link đăng nhập | Thêm QCVN 34:2022/BTTTT (thay thế QCVN 34:2019/BTTTT); đổi link E.812 sang trang công khai |
| 12 | API chưa có cách trả nhãn "Dữ liệu mô phỏng" và mức chất lượng | View `v_kpi_values_classified` trả sẵn `quality_level` và `data_nature` |

# 1. Bộ 8 KPI sử dụng cho mạng cố định

Giữ 6 KPI chất lượng truy cập Internet và bổ sung 2 chỉ số HTTP theo ETSI TS 103 222-2. RSRP và SINR được loại vì là chỉ số tín hiệu mạng di động.

| **#** | **Tên KPI** | **kpi_code** | **Đơn vị** | **Chiều tốt** | **Tỷ lệ** | **Cách tổng hợp tuần** |
|----|----|----|----|----|----|----|
| 1 | Download Throughput | download_throughput | Mbps | Cao tốt | Không | Trung vị các phép đo hợp lệ |
| 2 | Upload Throughput | upload_throughput | Mbps | Cao tốt | Không | Trung vị các phép đo hợp lệ |
| 3 | Latency (RTT) | latency | ms | Thấp tốt | Không | Trung vị các phép đo hợp lệ |
| 4 | Jitter | jitter | ms | Thấp tốt | Không | Trung vị các phép đo hợp lệ |
| 5 | Packet Loss Rate | packet_loss_rate | % | Thấp tốt | Có | Tổng gói mất / tổng gói gửi × 100 |
| 6 | Network Availability | network_availability | % | Cao tốt | Có | Tổng thời gian sẵn sàng / tổng thời gian giám sát × 100 |
| 7 | HTTP IP-Service Access Failure Ratio | http_ip_access_failure_ratio | % | Thấp tốt | Có | Tổng lần thiết lập thất bại / tổng lần thử × 100 |
| 8 | HTTP Dropped Sessions Ratio | http_dropped_sessions_ratio | % | Thấp tốt | Có | Tổng phiên bị ngắt / tổng phiên × 100 |

KPI tỷ lệ (cột "Tỷ lệ" = Có) lưu kèm tử số và mẫu số. Tử số và mẫu số cộng dồn được, nên giá trị tuần tính đúng từ dữ liệu gốc. Bốn KPI trung vị thì không cộng dồn được; đây là lý do V2.1 không tổng hợp lên tháng.

## Vì sao chọn 2 KPI HTTP này?

- HTTP IP-Service Access Failure Ratio đo tỷ lệ lần thử không thiết lập được kết nối TCP/IP tới máy chủ dịch vụ, đại diện cho khả năng truy cập dịch vụ.
- HTTP Dropped Sessions Ratio đo tỷ lệ phiên HTTP bị ngắt ngoài ý muốn sau khi đã bắt đầu, đại diện cho khả năng duy trì phiên.
- ETSI TS 103 222-2 V1.3.1 (02/2025) liệt kê hai chỉ số này trong bộ KPI tham chiếu cho Internet tốc độ cao. Đây là căn cứ chọn KPI, không phải ngưỡng tốt/trung bình/kém. Vũ cần đối chiếu số bảng và số mục ETSI trước khi trích vào báo cáo.

Lưu ý thuật ngữ: không gọi chung là Accessibility Rate / Retainability Rate, vì hai tên này thường dùng cho KPI mạng di động theo 3GPP.

# 2. Nguyên tắc không gian và thời gian

## 2.1. Phạm vi nghiên cứu

| **Thông số** | **Giá trị** |
|----|----|
| Mã khung | HCM-CENTER-NE |
| Hình dạng | Hình chữ nhật trong EPSG:32648 (UTM 48N) |
| Tọa độ | X 683.000 – 698.000 m; Y 1.190.000 – 1.201.000 m |
| Kích thước | 15 km (Đông–Tây) × 11 km (Bắc–Nam) = 165 ô 1 km |
| Khu vực bao gồm | Bến Thành (ô G1K-685-1191), Thủ Thiêm, Thảo Điền, An Phú, một phần Thủ Đức cũ (ô G1K-693-1199) |

Lý do: khung chứa cả lõi đô thị, khu dân cư mới và vùng ven, nên dữ liệu mô phỏng có thể thể hiện chênh lệch chất lượng giữa các khu. 165 ô đủ để bản đồ có ý nghĩa mà vẫn nhẹ cho Frontend.

Giới hạn: khung có một đoạn sông Sài Gòn, các ô chủ yếu là mặt nước nên có ít mẫu hơn trong bộ mô phỏng (giả định này ghi trong `data_sources.assumptions`). Từ 01/07/2025 TP.HCM không còn cấp quận; báo cáo gọi khu vực theo tên địa danh hoặc phường mới, không dùng "Quận 1", "Quận 2".

Đổi khung: chỉ sửa 4 số trong `ST_MakeEnvelope` của file SQL rồi chạy lại bước sinh lưới. Mã các ô cũ không đổi.

## 2.2. Không gian: lưới vuông 1 km × 1 km

- Sinh lưới bằng `ST_SquareGrid(1000, …)` trong EPSG:32648, lưu hình học ở EPSG:4326 để trả GeoJSON.
- `grid_col` = `i`, `grid_row` = `j` của `ST_SquareGrid`, gốc mặc định (0,0) của EPSG:32648. Nhờ vậy mã ô không đổi khi nạp lại hoặc mở rộng khung. Không đổi CRS, kích thước ô hay gốc lưới.
- Mã ô: `G1K-<i>-<j>`, ví dụ `G1K-685-1191`. API và Frontend chỉ dùng `region_code`, không dùng `region_id`.
- Giữ ô vuông nguyên vẹn, không cắt theo ranh giới. Chỉ lấy ô có phần trong giao với khung (`ST_Intersects` và không chỉ chạm cạnh).
- Dữ liệu dạng điểm (nếu bộ mô phỏng sinh điểm) được gán vào đúng một ô chứa điểm, rồi tổng hợp theo tuần.
- Phương án dự phòng: lưới 500 m (`grid_500m`, mã `G500-<i>-<j>`) hoặc phường/xã (`ward`). Schema đã nhận cả hai, không cần sửa bảng.

## 2.3. Thời gian: theo tuần trong 26 tuần

| **Quy tắc** | **Giá trị** |
|----|----|
| Chu kỳ | Tuần (`week`) |
| Định nghĩa tuần | Thứ Hai đến Chủ nhật |
| Giá trị lưu | `period_start` = ngày thứ Hai đầu tuần |
| Khoảng dữ liệu | 26 tuần, tuần đầu 04/05/2026, tuần cuối 26/10/2026 – 01/11/2026 |
| Mức tổng hợp | Mỗi nguồn × ô × KPI × tuần có tối đa một giá trị |

Lý do chọn tuần: 26 điểm mỗi ô đủ để vẽ xu hướng và so sánh hai kỳ, trong khi theo tháng chỉ có 6 điểm. Không tổng hợp lên tháng vì giá trị trung vị không cộng dồn được.

Quy tắc bắt buộc: `period_start` luôn là thứ Hai và nằm trong khoảng `period_from` – `period_to` của nguồn dữ liệu. CSDL chặn cả hai trường hợp sai.

# 3. Nguyên tắc xây dựng dữ liệu mô phỏng

| **Thành phần cần mô tả** | **Yêu cầu** | **Lưu ở** |
|----|----|----|
| Phạm vi không gian | Khung HCM-CENTER-NE, lưới 1 km | `study_areas`, `data_sources.spatial_scope` |
| Phạm vi thời gian | 04/05/2026 – 01/11/2026, 26 tuần | `data_sources.period_from/period_to` |
| Phương pháp tạo | Thuật toán, bộ tham số, cách tổng hợp | `collection_method`, `method_version` |
| Tái tạo được | Seed ngẫu nhiên cố định | `random_seed` |
| Giả định | Mức chất lượng nền theo khu, biến động theo tuần, tải giả định; chỉ ghi giả định thực sự áp dụng | `assumptions` |
| Tính hợp lý | Giá trị trong miền hợp lệ; không sinh số ngẫu nhiên không quy tắc | Trigger kiểm miền |
| Quan hệ KPI | Có thể đặt quan hệ có kiểm soát (ví dụ latency tăng thì jitter tăng); ghi rõ là giả định mô phỏng | `assumptions` |
| Giới hạn | Không phải số liệu đo của VNPT; không dùng kết luận chất lượng mạng thực tế | `limitations` |

## 3.1. Quy tắc lưu nguồn dữ liệu

- Bộ mô phỏng có một bản ghi `data_sources` với `source_type = simulation`, `data_nature = simulated`. CSDL chặn trường hợp `simulation` mà ghi `real`.
- Mọi bản ghi `kpi_values` phải có `source_id`.
- Có thể lưu song song nhiều nguồn (ví dụ một bộ mô phỏng và một bộ công khai) để so sánh. Chỉ một nguồn có `is_default = TRUE`; API dùng nguồn này khi Frontend không chỉ định.
- Báo cáo, giao diện và chú giải bản đồ hiển thị nhãn "Dữ liệu mô phỏng" khi `data_nature = simulated`.

## 3.2. Ngưỡng phân loại tốt / trung bình / kém

- Mỗi KPI có đúng 3 mức `good`, `medium`, `poor`, cùng đơn vị với KPI.
- Quy ước khoảng nửa mở `[min_value, max_value)`. Mức ở hai đầu để trống một cận:
  - KPI cao tốt: `poor [NULL, a)` — `medium [a, b)` — `good [b, NULL)`
  - KPI thấp tốt: `good [NULL, a)` — `medium [a, b)` — `poor [b, NULL)`
- `threshold_type = standard` bắt buộc có `reference_name`. Ngưỡng nhóm tự đề xuất ghi `team_proposed` và nêu phương pháp trong `threshold_basis`.
- Sau khi nạp ngưỡng, chạy `SELECT * FROM v_kpi_threshold_check;` — mọi KPI phải trả `ok`.
- V2.1 chưa điền số ngưỡng. Không tự đặt số rồi gọi là ngưỡng chuẩn hoặc ngưỡng VNPT.

Network Availability và hai KPI HTTP không đồng nghĩa: Availability là tỷ lệ thời gian kết nối sẵn sàng; HTTP access failure là tỷ lệ lần thử thiết lập kết nối thất bại; HTTP dropped sessions là tỷ lệ phiên bị ngắt sau khi đã bắt đầu.

# 4. Mô hình dữ liệu

| **Bảng / View** | **Vai trò** | **Quan hệ** |
|----|----|----|
| study_areas | Khung phạm vi nghiên cứu dùng để sinh lưới | 1 khung → N regions |
| regions | Ô lưới 1 km (dự phòng: 500 m, phường/xã) | 1 region → N kpi_values |
| kpis | Danh mục 8 KPI, đơn vị, chiều tốt, miền hợp lệ, cách tính | 1 KPI → N kpi_values, N kpi_thresholds |
| kpi_thresholds | Khoảng ngưỡng 3 mức và căn cứ | N → 1 KPI |
| data_sources | Mô tả nguồn, khoảng thời gian, phương pháp, giả định, giới hạn | 1 nguồn → N kpi_values |
| kpi_values | Giá trị KPI theo nguồn × ô × tuần | N → 1 region, 1 KPI, 1 nguồn |
| v_kpi_values_classified | Giá trị kèm `quality_level` và `data_nature`, dùng cho API | View |
| v_kpi_threshold_check | Kiểm tra ngưỡng đủ mức, không hở, đúng chiều | View |

## 4.1. Sơ đồ quan hệ

```
study_areas (1) ── (N) regions (1) ── (N) kpi_values (N) ── (1) kpis (1) ── (N) kpi_thresholds
                                            │
                                           (N)
                                            │
                                      (1) data_sources
```

## 4.2. Quy ước thiết kế

- Khóa chính BIGSERIAL; khóa ngoại bảo đảm liên kết.
- `region_code`, `kpi_code`, `source_code` là mã nghiệp vụ ổn định để API, Frontend và file dữ liệu trao đổi; không dùng khóa tự tăng làm mã trao đổi.
- `geom` là `geometry(MultiPolygon, 4326) NOT NULL`, có CHECK `ST_IsValid` và index GiST.
- `kpi_values` lưu giá trị đã tổng hợp theo tuần, không lưu từng phép đo thô.

# 5. Thiết kế chi tiết các bảng

## 5.1. study_areas — Phạm vi nghiên cứu

| **Trường** | **Kiểu** | **Ràng buộc / ý nghĩa** |
|----|----|----|
| area_id | BIGSERIAL | PK |
| area_code | TEXT | UNIQUE, NOT NULL — ví dụ HCM-CENTER-NE |
| area_name | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL — tọa độ khung và khu vực bao gồm |
| geom | geometry(MultiPolygon,4326) | NOT NULL, hợp lệ |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

## 5.2. regions — Ô lưới địa lý

| **Trường** | **Kiểu** | **Ràng buộc / ý nghĩa** |
|----|----|----|
| region_id | BIGSERIAL | PK — khóa nội bộ |
| region_code | TEXT | UNIQUE, NOT NULL — `G1K-<i>-<j>` |
| region_name | VARCHAR(255) | NOT NULL — ví dụ "Ô 685-1191" |
| region_level | VARCHAR(20) | NOT NULL, mặc định `grid_1km`; nhận `grid_1km`, `grid_500m`, `ward` |
| parent_region_id | BIGINT | FK → regions, có thể NULL — dùng khi gắn ô vào phường/xã |
| area_id | BIGINT | FK → study_areas |
| grid_col / grid_row | INTEGER | `i`, `j` của ST_SquareGrid; bắt buộc khi là lưới, NULL khi là phường/xã; UNIQUE (region_level, grid_col, grid_row) |
| grid_size_m | SMALLINT | 1000 với `grid_1km`, 500 với `grid_500m`, NULL với `ward` |
| geom | geometry(MultiPolygon,4326) | NOT NULL, hợp lệ, index GiST |
| created_at / updated_at | TIMESTAMPTZ | DEFAULT NOW() |

## 5.3. kpis — Danh mục KPI

| **Trường** | **Kiểu** | **Ràng buộc / ý nghĩa** |
|----|----|----|
| kpi_id | BIGSERIAL | PK |
| kpi_code | TEXT | UNIQUE, NOT NULL — mã API |
| kpi_name | VARCHAR(180) | NOT NULL |
| kpi_group | VARCHAR(50) | NOT NULL — internet_performance, internet_stability, availability, service_access, session_continuity |
| unit | VARCHAR(30) | NOT NULL — Mbps, ms hoặc % |
| higher_is_better | BOOLEAN | NOT NULL — chiều đánh giá và chiều thang màu |
| is_ratio | BOOLEAN | NOT NULL — TRUE khi unit = % (CHECK đồng bộ) |
| valid_min / valid_max | NUMERIC(18,6) | Miền hợp lệ; mặc định min = 0; % có max = 100; NULL = không giới hạn |
| description / calculation_method / aggregation_method | TEXT | NOT NULL |
| reference_name | TEXT | Tài liệu định nghĩa KPI |
| display_order | SMALLINT | NOT NULL — thứ tự hiển thị trên Frontend |
| is_active | BOOLEAN | DEFAULT TRUE |

## 5.4. kpi_thresholds — Ngưỡng phân loại

| **Trường** | **Kiểu** | **Ràng buộc / ý nghĩa** |
|----|----|----|
| threshold_id | BIGSERIAL | PK |
| kpi_id | BIGINT | FK → kpis, NOT NULL |
| quality_level | VARCHAR(10) | good, medium hoặc poor |
| min_value / max_value | NUMERIC(18,6) | Khoảng `[min, max)`; một đầu có thể NULL, không được cả hai; min < max |
| threshold_type | VARCHAR(20) | standard hoặc team_proposed |
| threshold_basis | TEXT | NOT NULL — căn cứ hoặc phương pháp nhóm tự đề xuất |
| reference_name / reference_url | TEXT | Bắt buộc `reference_name` khi `standard` |
| notes | TEXT | Giả định, lưu ý |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

Ràng buộc: UNIQUE (kpi_id, quality_level); EXCLUDE chặn hai khoảng chồng lấn trong cùng một KPI. Việc phủ đủ miền và đúng chiều kiểm bằng `v_kpi_threshold_check`.

## 5.5. data_sources — Nguồn dữ liệu

| **Trường** | **Kiểu** | **Ràng buộc / ý nghĩa** |
|----|----|----|
| source_id | BIGSERIAL | PK |
| source_code | TEXT | UNIQUE, NOT NULL — ví dụ SIM-V1 |
| source_name | VARCHAR(255) | NOT NULL |
| source_type | VARCHAR(40) | simulation, public_dataset, field_measurement, company_data, other |
| data_nature | VARCHAR(20) | real hoặc simulated; `simulation` bắt buộc `simulated` |
| description / spatial_scope | TEXT | NOT NULL |
| period_from / period_to | DATE | NOT NULL; from là thứ Hai, to là Chủ nhật |
| collection_method | TEXT | NOT NULL |
| method_version / random_seed | TEXT / BIGINT | Phiên bản script và seed để tái tạo dữ liệu |
| assumptions / limitations | TEXT | NOT NULL |
| source_url | TEXT | Liên kết tham khảo nếu có |
| is_default | BOOLEAN | Chỉ một nguồn được TRUE |
| created_at / updated_at | TIMESTAMPTZ | DEFAULT NOW() |

## 5.6. kpi_values — Giá trị KPI theo nguồn × ô × tuần

| **Trường** | **Kiểu** | **Ràng buộc / ý nghĩa** |
|----|----|----|
| kpi_value_id | BIGSERIAL | PK |
| source_id / region_id / kpi_id | BIGINT | FK, NOT NULL |
| period_type | VARCHAR(10) | Cố định `week` |
| period_start | DATE | NOT NULL; thứ Hai; nằm trong khoảng của nguồn |
| value | NUMERIC(18,6) | Có khi `ok`; NULL khi `missing`/`invalid`; trong miền hợp lệ của KPI |
| status | VARCHAR(10) | ok, missing, invalid |
| sample_count | INTEGER | ≥ 0; > 0 khi `ok` |
| numerator_value / denominator_value | NUMERIC(20,6) | Bắt buộc với KPI tỷ lệ khi `ok`; đi cùng nhau; mẫu > 0; 0 ≤ tử ≤ mẫu; `value` = tử/mẫu × 100 |
| quality_note | TEXT | Bắt buộc khi `invalid` |
| updated_at | TIMESTAMPTZ | Tự cập nhật khi ghi |

# 6. Quy tắc dữ liệu và kiểm thử

| **Quy tắc** | **Cơ chế** |
|----|----|
| Một giá trị cho mỗi nguồn/KPI/ô/tuần | UNIQUE (source_id, kpi_id, period_start, region_id) |
| Thiếu dữ liệu không phải 0 | CHECK: `missing` thì `value` NULL; 0 chỉ là giá trị đo/mô phỏng thật |
| Dữ liệu không hợp lệ | CHECK: `invalid` thì `value` NULL và phải có `quality_note` |
| Truy nguyên nguồn | `source_id` NOT NULL; view trả `data_nature` |
| Tỷ lệ khớp tử/mẫu | Trigger `kpi_values_validate` |
| Miền giá trị | Trigger theo `kpis.valid_min/valid_max` (tỷ lệ 0–100, còn lại ≥ 0) |
| Tuần hợp lệ | CHECK thứ Hai; trigger kiểm nằm trong khoảng của nguồn |
| Ngưỡng không chồng lấn | EXCLUDE trên `numrange` (cần extension `btree_gist`) |
| Ngưỡng đủ mức, đúng chiều | `v_kpi_threshold_check` |

## 6.1. Chỉ mục

- GiST trên `regions.geom` cho truy vấn theo khung nhìn bản đồ.
- UNIQUE (source_id, kpi_id, period_start, region_id) phục vụ luôn truy vấn bản đồ: một KPI, một tuần, mọi ô.
- B-tree (source_id, region_id, kpi_id, period_start) phục vụ lịch sử KPI của một ô.

## 6.2. Kết quả chạy thử

Đã chạy toàn bộ file SQL trên PostgreSQL 16 + PostGIS 3.4.2 (các hàm dùng đều có từ PostGIS 3.1, chạy được trên bản 17 + 3.5.2 của nhóm; Backend sẽ chạy lại trên sandbox chính thức).

- Tạo đủ 6 bảng, 2 view, 1 trigger. Sinh 165 ô, tổng diện tích đúng 165 km², tất cả hợp lệ và là MultiPolygon.
- Ô G1K-685-1191 chứa chợ Bến Thành; ô G1K-693-1199 nằm ở Thủ Đức cũ.
- Dữ liệu hợp lệ nạp được; view trả đúng `quality_level` và `data_nature = simulated`.
- 14 trường hợp sai đều bị chặn: ngày không phải thứ Hai, `ok` thiếu giá trị, `missing` có số, bản ghi trùng, tỷ lệ > 100%, giá trị lệch tử/mẫu, KPI tỷ lệ thiếu tử/mẫu, throughput âm, tuần ngoài khoảng nguồn, `invalid` thiếu ghi chú, ngưỡng chồng lấn, ngưỡng `standard` thiếu tài liệu, nguồn `simulation` ghi `real`, hai nguồn mặc định.

Ngoài phạm vi V2.1: bảng `import_batches` (nhật ký nhập file). Chỉ thêm khi làm chức năng nhập file.

# 7. Tệp SQL và cách triển khai

Tệp `N4.6_Database_Schema_V2.1.sql` gồm: extension, 6 bảng, ràng buộc, index, trigger, 2 view, 8 KPI, khung nghiên cứu, bước sinh 165 ô và một nguồn mô phỏng `SIM-V1` (các trường phương pháp, giả định để Vũ điền). Chú thích trong file viết không dấu để tránh lỗi mã hóa khi chạy `psql` trên Windows.

Chạy: `psql -d <db> -v ON_ERROR_STOP=1 -f N4.6_Database_Schema_V2.1.sql`

## 7.1. Thứ tự triển khai

1. Backend (An): chạy SQL trên sandbox; chuyển API sang `v_kpi_values_classified`, thêm `data_nature` và `quality_level` vào phản hồi, thêm tham số `source` (mặc định nguồn `is_default`).
2. Data/QA (Vũ): viết script sinh dữ liệu cho 165 ô × 8 KPI × 26 tuần (~34.000 dòng), điền phương pháp và giả định vào `SIM-V1`.
3. An + Vũ: tra cứu ngưỡng, nạp `kpi_thresholds`, chạy `v_kpi_threshold_check`.
4. Leader (Đạt): rà soát KPI, đơn vị, nguồn, ngưỡng; cập nhật tài liệu khi có góp ý.
5. Frontend (Đức): dùng `region_code`, `kpi_code`, `period_start`, `quality_level`, `higher_is_better` cho bản đồ và chú giải; hiện nhãn "Dữ liệu mô phỏng" theo `data_nature`.

# 8. Tài liệu tham khảo kỹ thuật

**QCVN 34:2022/BTTTT** — Quy chuẩn kỹ thuật quốc gia về chất lượng dịch vụ truy nhập Internet băng rộng cố định mặt đất (ban hành kèm Thông tư 20/2022/TT-BTTTT, thay thế QCVN 34:2019/BTTTT).
> Căn cứ chính cho ngưỡng KPI tốc độ của mạng cố định tại Việt Nam. Cần đọc bản gốc để trích đúng điều, mục.

**ETSI TS 103 222-2 V1.3.1 (2025-02)** — Reference benchmarking and KPIs for High speed internet.
> https://www.etsi.org/deliver/etsi_ts/103200_103299/10322202/01.03.01_60/ts_10322202v010301p.pdf
> Định nghĩa HTTP IP Service Access Failure Ratio và HTTP Dropped Sessions.

**ITU-T Y.1540 (12/2019)** — IP packet transfer and availability performance parameters.
> https://www.itu.int/rec/T-REC-Y.1540/en
> Định nghĩa độ trễ (IPTD), biến thiên độ trễ (IPDV), tỷ lệ mất gói (IPLR) và tính sẵn sàng.

**ITU-T E.812 (2020) Amendment 1** — Crowdsourcing approach for the assessment of end-to-end QoS in fixed and mobile broadband networks.
> https://www.itu.int/rec/T-REC-E.812/en
> Cách tiếp cận thu thập dữ liệu cho băng rộng cố định; tham khảo khi mô tả phương pháp mô phỏng.

Giới hạn: việc ETSI/ITU liệt kê một chỉ số không có nghĩa ngưỡng tốt/trung bình/kém của đồ án đã được chuẩn hóa. Mỗi ngưỡng phải dẫn căn cứ riêng.
