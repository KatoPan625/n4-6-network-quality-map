# N4.6 — Database Schema

**Bản đồ số hiển thị chất lượng mạng theo khu vực**  
**Phạm vi:** Mạng di động 4G · Cell / giờ · 30 ngày  
**CSDL:** PostgreSQL + PostGIS  
**Schema PostgreSQL:** `n46`  
**Trạng thái:** Đã chạy và kiểm thử trên PostgreSQL 17 + PostGIS 3.5 ngày 19/11/2026 (Backend): tạo đối tượng, ràng buộc, tổng hợp, materialized view.

---

## 1. Các quyết định thiết kế

| Nội dung | Quyết định |
|---|---|
| Công nghệ mạng giai đoạn 1 | Chỉ nạp 4G (`rat = '4G'`); schema cho phép `4G` và `5G` để mở rộng sau (`DEFAULT '4G'`) |
| Phạm vi hành chính | 34 tỉnh/thành trên toàn quốc; dữ liệu phường/xã chi tiết chỉ cho TP.HCM (168 đơn vị) |
| Quy mô cell | Khoảng 1.000 cell mô phỏng |
| Khoảng thời gian ví dụ | 01/10/2026 00:00 đến trước 31/10/2026 00:00, giờ `Asia/Ho_Chi_Minh` (720 giờ) |
| Độ phân giải thời gian | Theo giờ; lưu `TIMESTAMPTZ` |
| Bộ KPI ban đầu | `cssr`, `service_drop_all`, `user_throughput`, `traffic` |
| Bản chất dữ liệu | Mô phỏng; `data_nature = 'simulated'` |
| Tọa độ trạm/cell | Không lưu tọa độ trạm. Cell liên kết với tỉnh và, khi có dữ liệu chi tiết, với phường/xã |
| Cách trao đổi giữa Backend / Frontend / file dữ liệu | Dùng các mã ổn định như `region_code`, `cell_code`, `kpi_code`, `source_code`; không dùng ID tự tăng làm mã trao đổi |

> **Lưu ý:** `period_to` là mốc kết thúc không bao gồm (exclusive). Ví dụ 01–30/10/2026 được lưu dưới dạng `[2026-10-01 00:00 +07, 2026-10-31 00:00 +07)`, tương ứng 720 giờ.

## 2. Quyết định chi tiết

1. **KPI được lưu trực tiếp:** `cell_kpi_values` lưu giá trị KPI cuối cùng tại từng cell/giờ. Không lưu counter thành phần trong CSDL. Cách tính được mô tả trong `kpis.calculation_method`; dữ liệu mô phỏng sinh trực tiếp giá trị KPI ở cấp cell.
2. **Mẫu số Traffic:** KPI chất lượng chỉ dùng những cell có cả KPI hợp lệ và Traffic hợp lệ tại cùng cell, cùng giờ. Traffic của cell bị thiếu KPI không được đưa vào mẫu số. Đây là cách tính đúng vì nếu tử số bỏ cell thiếu KPI nhưng mẫu số vẫn cộng Traffic của cell đó thì kết quả sẽ bị kéo thấp sai lệch.
3. **Cell có Traffic bằng 0:** vẫn được tính là cell đã báo cáo nếu KPI và bản ghi Traffic đều hợp lệ; Traffic bằng 0 không đóng góp vào tử số hoặc mẫu số có trọng số. Nếu toàn vùng không có Traffic dương, giá trị tổng hợp là `NULL` và `aggregation_status = 'no_positive_traffic'`.
4. **Đơn vị Traffic:** dùng GB thập phân, `1 GB = 10^9 byte`; không dùng GiB.
5. **Cell – phường – tỉnh:** `province_id` bắt buộc. `ward_id` được phép `NULL` tại tỉnh chưa nạp dữ liệu phường. Tại tỉnh đã có dữ liệu phường (TP.HCM), mọi cell bắt buộc có `ward_id`; nếu có `ward_id`, phường phải thuộc đúng tỉnh trong `province_id`. Các quy tắc này được kiểm tra bằng trigger.
6. **Trạng thái cell:** dùng `is_active`. Danh sách cell và trạng thái hoạt động được giả định cố định trong toàn bộ 30 ngày mô phỏng; không thêm `active_from` / `active_to` ở phạm vi demo.
7. **Namespace PostgreSQL:** dùng tên cố định `n46`; số phiên bản chỉ xuất hiện trong tài liệu và tên file SQL, không tạo schema mới theo từng phiên bản.
8. **RAT:** `rat` có `CHECK (rat IN ('4G','5G'))`, mặc định `4G`. Giai đoạn 1 chỉ nạp cell 4G.
9. **Index truy vấn giờ:** bổ sung index `(source_id, kpi_id, period_start)` trên `cell_kpi_values` để truy vấn một KPI tại một giờ trên toàn bộ cell.
10. **View và phân loại:** giữ hai view nghiệp vụ `v_region_kpi` (theo giờ) và `v_region_kpi_daily` (theo ngày). Mỗi view `LEFT JOIN kpi_thresholds` để trả thêm `quality_level` và `threshold_type`. Giữ `v_kpi_threshold_check`; bỏ hai view classified riêng.
11. **Trạng thái cho API:** hai view giữ `status` và `aggregation_status`. API gộp theo hợp đồng Frontend: trả `status` thuộc `ok/partial/missing`; khi `aggregation_status = 'no_positive_traffic'`, API trả `value = NULL` và `reason = 'no_positive_traffic'`. Đây là mapping ở API, không cần thêm cột trong CSDL.
12. **Tham chiếu 3GPP:** dùng `3GPP TS 32.450 V19.0.0 (2025-10)` cho các mục A1, E-RAB Retainability và User Throughput theo phần mô tả KPI bên dưới.
13. **Phân loại vùng partial:** hai view gốc JOIN `kpi_thresholds` khi `a.value IS NOT NULL`, không phụ thuộc `a.status = 'ok'`. Vì vậy vùng `partial` vẫn có `quality_level` nếu có giá trị tổng hợp; `status` vẫn giữ là `partial`.
14. **Tăng tốc truy vấn:** bổ sung `mv_region_kpi` và `mv_region_kpi_daily` để API đọc kết quả tổng hợp đã tính sẵn. Hai MV được refresh sau khi nạp dữ liệu mô phỏng và ngưỡng; không refresh tự động.

## 3. Danh mục KPI và cách tính

| `kpi_code` | Tên hiển thị | Đơn vị | Quy tắc tổng hợp vùng | Chiều tốt |
|---|---|---:|---|---|
| `cssr` | Call Setup Success Rate (CSSR) | % | Traffic-weighted | Cao hơn tốt hơn |
| `service_drop_all` | Service Drop All | % | Traffic-weighted | Thấp hơn tốt hơn |
| `user_throughput` | User Throughput (Downlink) | Mbps | Traffic-weighted | Cao hơn tốt hơn |
| `traffic` | Traffic Volume | GB | SUM | Không áp dụng |

### 3.1 CSSR (tên Mentor sử dụng; 3GPP gọi là A1)

Theo `3GPP TS 32.450 V19.0.0 (2025-10)`, mục 6.1.1, tên chỉ số trong tài liệu 3GPP là **A1 – Initial E-RAB establishment success rate**. Mentor dùng tên CSSR; trong tài liệu kỹ thuật cần ghi rõ CSSR là tên Mentor sử dụng cho chỉ số tương ứng với A1.

```text
CSSR (%) =
    (ΣRRC.ConnEstabSucc / ΣRRC.ConnEstabAtt)
  × (S1SIG.ConnEstabSucc / S1SIG.ConnEstabAtt)
  × (ΣERAB.EstabInitSuccNbr / ΣERAB.EstabInitAttNbr)
  × 100
```

- Các tỷ số thành phần được hiểu là tỷ lệ thập phân; kết quả cuối cùng biểu diễn theo phần trăm.
- Đây là KPI được mô phỏng trực tiếp ở cấp cell/giờ và lưu vào `cell_kpi_values.value`.
- Không lưu counter thành phần RRC/S1/E-RAB trong CSDL.
- `calculation_method` của KPI lưu công thức và tham chiếu A1 để bảo đảm tiêu chí nghiệm thu về cách tính rõ ràng.

### 3.2 Service Drop All

```text
Service Drop All (%) =
    số E-RAB giải phóng bất thường khi vẫn còn dữ liệu trong buffer
    / tổng số E-RAB giải phóng
    × 100
```

- Đây là **định nghĩa dạng phần trăm theo thực tiễn vận hành nhà mạng được nhóm lựa chọn; KHÔNG PHẢI công thức do 3GPP quy định**.
- `3GPP TS 32.450 V19.0.0 (2025-10)`, mục 6.2.1 định nghĩa E-RAB Retainability theo số lần giải phóng E-RAB bất thường trên thời gian phiên E-RAB (events/second). Đây là phép đo khác với tỷ lệ Service Drop All nêu trên; không ghi Service Drop All là công thức 3GPP.
- Dùng dạng phần trăm để nhân viên kỹ thuật giám sát dễ đọc và thiết lập ngưỡng.
- Nếu tổng số E-RAB giải phóng bằng 0, KPI không xác định: dữ liệu mô phỏng phải ghi `status = 'missing'`, `value = NULL`; không tự gán bằng 0.
- Giá trị KPI được mô phỏng trực tiếp ở cấp cell/giờ; không lưu counter trong CSDL.

### 3.3 User Throughput (Downlink)

Theo `3GPP TS 32.450 V19.0.0 (2025-10)`, mục 6.3.1:

```text
User Throughput (kbit/s) = ThpVolDl / ThpTimeDl
User Throughput (Mbps)   = (ThpVolDl / ThpTimeDl) / 1000
```

- 3GPP biểu diễn kết quả ở kbit/s; Schema lưu `Mbps`, nên chia kết quả kbit/s cho `1000`.
- Giá trị Mbps cuối cùng được mô phỏng trực tiếp ở cấp cell/giờ và lưu vào `cell_kpi_values.value`.
- Không lưu counter `ThpVolDl` hoặc `ThpTimeDl` trong CSDL.

### 3.4 Traffic

- `traffic`: lưu trực tiếp tổng lượng Traffic của cell trong một giờ, đơn vị GB thập phân (`1 GB = 10^9 byte`).
- Traffic được mô phỏng trực tiếp ở cấp cell/giờ; không lưu counter trong CSDL.
- Traffic là KPI tổng lượng, được cộng bằng `SUM` khi tổng hợp lên phường/tỉnh; với ba KPI chất lượng còn lại, Traffic là trọng số.

## 4. Nguyên tắc tổng hợp Cell → Phường / Tỉnh

### 4.1 KPI chất lượng

Với CSSR, Service Drop All và User Throughput:

```text
KPI_region(hour) =
    SUM(KPI_cell(hour) × Traffic_cell(hour))
    / SUM(Traffic_cell(hour))
```

Chỉ đưa vào tử số và mẫu số những cell có:

- KPI tại cell/giờ có `status = 'ok'` và `value` khác `NULL`;
- Traffic của chính cell đó, cùng giờ và cùng nguồn có `status = 'ok'` và `value` khác `NULL`.

Traffic dương (`> 0`) mới đóng góp trọng số. Traffic bằng 0 vẫn được xem là dữ liệu Traffic đã báo cáo nhưng không làm thay đổi trung bình có trọng số.

**Không** đưa Traffic của cell bị thiếu KPI vào mẫu số. Phần thiếu được phản ánh bằng `status = 'partial'` và số lượng cell báo cáo.

### 4.2 KPI Traffic

```text
Traffic_region(hour) = SUM(Traffic_cell(hour))
```

Cộng tất cả giá trị Traffic hợp lệ trong phạm vi vùng/giờ, độc lập với việc cell đó có đủ các KPI chất lượng khác hay không.

### 4.3 Chỉ số độ phủ dữ liệu

- `cells_total`: tổng số cell `is_active` được gán vào vùng.
- `cells_reported`: số cell có giá trị KPI hợp lệ và, với KPI traffic-weighted, có thêm Traffic hợp lệ tại cùng cell/giờ. Traffic bằng 0 vẫn được tính là đã báo cáo.
- `cells_weighted`: số cell có KPI hợp lệ và Traffic dương, thực sự đóng góp vào trung bình có trọng số.
- `status = 'missing'`: không có cell nào báo cáo hợp lệ cho KPI đó.
- `status = 'partial'`: có dữ liệu nhưng số cell báo cáo ít hơn `cells_total`.
- `status = 'ok'`: tất cả cell trong vùng báo cáo hợp lệ cho KPI đó.
- `aggregation_status = 'no_positive_traffic'`: có KPI và Traffic hợp lệ nhưng tổng Traffic dương để làm trọng số bằng 0; giá trị tổng hợp để `NULL`.

Trạng thái được tính **riêng cho từng KPI**.

## 5. Quy tắc không gian và liên kết Cell

### 5.1 `regions`

Lưu ranh giới hành chính bằng GeoJSON/PostGIS:

- `region_level = 'province'`: 34 tỉnh/thành.
- `region_level = 'ward'`: 168 phường/xã thuộc TP.HCM trong phạm vi dữ liệu chi tiết.
- Phường/xã liên kết lên tỉnh qua `parent_region_id`.
- `region_code` sử dụng mã hành chính chính thức; không dùng tên địa phương làm khóa liên kết.
- Hình học lưu dưới dạng `geometry(MultiPolygon, 4326)`, có kiểm tra hình học hợp lệ và GiST index.

### 5.2 `cells`

| Trường | Vai trò |
|---|---|
| `cell_id` | Khóa nội bộ |
| `cell_code` | Mã cell ổn định, duy nhất |
| `province_id` | Bắt buộc; FK đến một region cấp tỉnh |
| `ward_id` | FK đến phường/xã; nullable chỉ khi tỉnh chưa có dữ liệu ward-level |
| `rat` | Cho phép `4G` hoặc `5G`; mặc định `4G`, giai đoạn 1 chỉ nạp `4G` |
| `is_active` | Cell có được tính trong toàn bộ khoảng mô phỏng hay không |
| `created_at`, `updated_at` | Thời điểm tạo/cập nhật |

Ràng buộc:

1. `province_id` phải trỏ đến `regions.region_level = 'province'`.
2. Nếu `ward_id` có giá trị, region đó phải có `region_level = 'ward'` và `parent_region_id = province_id`.
3. Nếu tỉnh có ít nhất một region cấp phường/xã, cell thuộc tỉnh đó bắt buộc có `ward_id`.
4. Nếu thêm ward sau khi đã nạp cell không có `ward_id` cho tỉnh đó, trigger sẽ từ chối thao tác; cần nạp tỉnh và các phường/xã trước, sau đó mới nạp cell.
5. Không lưu latitude/longitude hoặc tọa độ trạm/cell.

### 5.3 Nguồn ranh giới

- Nguồn chính do nhóm cung cấp: Hugging Face `myleo198/sapnhap-bando-vn`; giấy phép hiển thị CC BY-NC 4.0. Cần ghi attribution và không dùng cho mục đích thương mại nếu chưa có quyền khác.
- Nguồn dự phòng: GitHub `thanglequoc/vietnamese-provinces-database`; cần kiểm tra lại độ cập nhật và giấy phép trước khi dùng thay thế.

## 6. Nguyên tắc thời gian và dữ liệu thiếu

### 6.1 Dữ liệu theo giờ

- `cell_kpi_values.period_start` dùng `TIMESTAMPTZ`.
- Thời gian được diễn giải theo `Asia/Ho_Chi_Minh`.
- `period_start` phải đúng đầu giờ địa phương (phút, giây bằng 0) và nằm trong khoảng nguồn dữ liệu `[period_from, period_to)`.
- Không tạo bảng ngày riêng. View ngày tính từ các bản ghi giờ bằng múi giờ của nguồn.

### 6.2 Dữ liệu thiếu / không hợp lệ

| `status` | `value` | Ý nghĩa |
|---|---|---|
| `ok` | Bắt buộc khác NULL | Có giá trị KPI hợp lệ |
| `missing` | Bắt buộc NULL | Không có dữ liệu KPI hoặc KPI không xác định (ví dụ mẫu số bằng 0) |
| `invalid` | Bắt buộc NULL | Bản ghi bị loại; phải có `quality_note` giải thích |

Không dùng số 0 để đại diện dữ liệu thiếu. Số 0 chỉ được lưu khi đó là giá trị đo/mô phỏng hợp lệ (ví dụ Traffic bằng 0).

## 7. Các bảng và View trong Schema

### 7.1 Các bảng

| Bảng | Chức năng |
|---|---|
| `regions` | 34 tỉnh/thành và 168 phường/xã TP.HCM; lưu ranh giới hành chính |
| `cells` | Danh mục khoảng 1.000 cell 4G; liên kết tỉnh và phường/xã nếu có |
| `data_sources` | Mô tả nguồn, bản chất dữ liệu, thời gian, không gian, cách mô phỏng, giả định và giới hạn |
| `kpis` | Danh mục KPI, đơn vị, chiều tốt, cách tổng hợp và cách tính |
| `kpi_thresholds` | Ngưỡng tốt/trung bình/kém và căn cứ; chưa seed ngưỡng số khi chưa có nguồn được xác nhận |
| `cell_kpi_values` | Giá trị KPI đã tính trực tiếp cho từng cell, KPI và giờ; không lưu counter |

### 7.2 Các View và Materialized View

| Đối tượng | Chức năng |
|---|---|
| `v_region_kpi` | View gốc tổng hợp KPI theo giờ từ cell lên phường/tỉnh; `LEFT JOIN kpi_thresholds` để trả `quality_level` và `threshold_type` |
| `v_region_kpi_daily` | View gốc tổng hợp ngày từ cell-hour theo lịch `Asia/Ho_Chi_Minh`; trạng thái dựa trên số cell-hour báo cáo / kỳ vọng; `LEFT JOIN kpi_thresholds` |
| `v_kpi_threshold_check` | Kiểm tra đủ 3 mức, khoảng ngưỡng không hở và đúng chiều tốt/xấu |
| `mv_region_kpi` | Materialized View chứa sẵn kết quả tổng hợp theo giờ; API dùng cho truy vấn giờ |
| `mv_region_kpi_daily` | Materialized View chứa sẵn kết quả tổng hợp theo ngày; API dùng cho truy vấn ngày |

Hai view classified riêng (`v_region_kpi_classified`, `v_region_kpi_daily_classified`) đã được bỏ. Hai view `v_region_kpi` và `v_region_kpi_daily` tiếp tục là nguồn logic chuẩn để đối chiếu/kiểm thử; API đọc từ hai Materialized View sau khi đã refresh.

**Phân loại vùng partial:** điều kiện JOIN ngưỡng là `a.value IS NOT NULL`, không phải `a.status = 'ok'`. Vì vậy nếu vùng có giá trị KPI tổng hợp nhưng trạng thái `partial`, vùng vẫn nhận `quality_level` và `threshold_type` để bản đồ có thể tô màu. `status` vẫn là `partial` để Frontend đồng thời thể hiện cảnh báo dữ liệu chưa đầy đủ. Nếu `value` là `NULL` (ví dụ không có traffic dương), vùng không được phân loại.

### 7.3 Materialized View, index và hiệu năng

Hai Materialized View được tạo theo cấu trúc:

- `mv_region_kpi`: `SELECT * FROM v_region_kpi`; dự kiến 581.760 dòng (202 vùng × 4 KPI × 720 giờ).
- `mv_region_kpi_daily`: `SELECT * FROM v_region_kpi_daily`; dự kiến 24.240 dòng (202 vùng × 4 KPI × 30 ngày).

Mỗi MV có hai index phục vụ hai dạng truy vấn chính:

| Materialized View | Index | Mục đích |
|---|---|---|
| `mv_region_kpi` | `(kpi_code, region_level, period_start)` | Một KPI, một cấp vùng, một thời điểm |
| `mv_region_kpi` | `(region_code, kpi_code, period_start)` | Lịch sử một KPI của một vùng |
| `mv_region_kpi_daily` | `(kpi_code, region_level, local_date)` | Một KPI, một cấp vùng, một ngày |
| `mv_region_kpi_daily` | `(region_code, kpi_code, local_date)` | Lịch sử một KPI của một vùng theo ngày |

**Quy trình refresh:** sau khi nạp hoàn tất `regions`, `cells`, `cell_kpi_values` và `kpi_thresholds`, chạy:

```sql
REFRESH MATERIALIZED VIEW n46.mv_region_kpi;
REFRESH MATERIALIZED VIEW n46.mv_region_kpi_daily;
ANALYZE n46.mv_region_kpi;
ANALYZE n46.mv_region_kpi_daily;
```

Refresh không chạy tự động. Vì bộ dữ liệu mô phỏng dự kiến nạp một lần, nhóm refresh sau lần nạp dữ liệu ban đầu; nếu cập nhật KPI/cell/nguồn/ngưỡng sau đó thì phải refresh lại cả hai MV. API không nên đọc MV trước khi refresh lần đầu.

**Benchmark do Backend cung cấp** (996 cell, 2.868.480 dòng `cell_kpi_values`, khoảng 832 MB):

| Truy vấn | View gốc | Materialized View |
|---|---:|---:|
| 1 giờ, 34 tỉnh | 20 ms | Chưa có số đo đối chiếu được cung cấp |
| 1 ngày, 168 phường | 1.222 ms | 0,1 ms |
| Chuỗi 30 ngày theo giờ, 1 phường | 10.721 ms | 0,7 ms |
| Chuỗi 30 ngày theo ngày, 1 tỉnh | 10.475 ms | 0,1 ms |

Theo kết quả Backend cung cấp, refresh cả hai MV mất khoảng 21 giây và kết quả được đối chiếu khớp 100% với view gốc. Đây là số đo từ môi trường thử nghiệm của Backend, không phải benchmark được chạy lại trong môi trường soạn tài liệu này.

**Quy ước API:** View và MV giữ `status` (`ok/partial/missing`) và `aggregation_status`. API có thể chuyển tiếp `status`; khi `aggregation_status = 'no_positive_traffic'`, API trả `value = NULL` và `reason = 'no_positive_traffic'`. Khi `status = 'partial'` nhưng `value IS NOT NULL`, API vẫn trả `quality_level` để Frontend tô màu, đồng thời hiển thị trạng thái dữ liệu partial.

## 8. Cấu trúc kỹ thuật chính

### 8.1 `cell_kpi_values`

| Trường | Ý nghĩa |
|---|---|
| `cell_kpi_value_id` | PK |
| `source_id` | FK đến `data_sources` |
| `cell_id` | FK đến `cells` |
| `kpi_id` | FK đến `kpis` |
| `period_start` | Giờ đo/tổng hợp (`TIMESTAMPTZ`) |
| `value` | Giá trị KPI cuối cùng; NULL khi missing/invalid |
| `status` | `ok`, `missing`, `invalid` |
| `quality_note` | Bắt buộc khi invalid |
| `updated_at` | Thời điểm cập nhật |

Khóa duy nhất: `(source_id, cell_id, kpi_id, period_start)`.

Index phục vụ truy vấn một KPI/mốc giờ trên toàn bộ cell: `(source_id, kpi_id, period_start)`. Index lịch sử cell được giữ riêng: `(cell_id, source_id, period_start, kpi_id)`.

### 8.2 `kpis`

Các trường quan trọng: `kpi_code`, `kpi_name`, `kpi_group`, `unit`, `higher_is_better`, `is_quality_kpi`, `is_ratio`, `aggregation_rule`, `valid_min`, `valid_max`, `description`, `calculation_method`, `reference_name`, `display_order`, `is_active`.

- `aggregation_rule = 'traffic_weighted'` cho CSSR, Service Drop All, User Throughput.
- `aggregation_rule = 'sum'` cho Traffic.
- `calculation_method` ghi đầy đủ công thức/định nghĩa và nêu rõ dữ liệu mô phỏng sinh trực tiếp KPI tại cấp cell.
- KPI mới có thể thêm bằng cách thêm dòng vào `kpis`; cấu trúc lưu dạng dọc không cần thêm cột KPI.

### 8.3 `data_sources`

Nguồn mô phỏng mẫu: `SIM-4G-2026-10`, `source_type = 'simulation'`, `data_nature = 'simulated'`, thời gian 30 ngày. `collection_method`, `assumptions` và `limitations` hiện là nội dung chờ Data/QA điền chi tiết theo thuật toán mô phỏng thực tế.

## 9. Giới hạn và giả định của Demo

1. Danh sách cell và `is_active` được coi là cố định trong toàn bộ 30 ngày. Schema không lưu lịch sử bật/tắt cell (`active_from`, `active_to`).
2. Giai đoạn 1 chỉ nạp cell 4G; ràng buộc Schema cho phép `rat` là `4G` hoặc `5G`, mặc định `4G`, để có thể mở rộng 5G về sau mà không cần migration chỉ vì giá trị RAT.
3. Cell không có tọa độ trạm; dữ liệu vùng được suy ra từ quan hệ hành chính.
4. KPI lưu trực tiếp là số liệu mô phỏng, không phải số liệu đo thực tế của VNPT và không được dùng để kết luận chất lượng mạng thực tế.
5. **Căn cứ công thức KPI:** CSSR được ghi rõ là tên Mentor sử dụng cho chỉ số A1 tham chiếu 3GPP TS 32.450 V19.0.0 mục 6.1.1. Service Drop All dùng định nghĩa phần trăm theo thực tiễn vận hành nhóm lựa chọn và phải ghi rõ không phải công thức 3GPP; mục 6.2.1 của 3GPP mô tả E-RAB Retainability theo đơn vị sự kiện/giây.
6. Mẫu số traffic-weighted loại cell thiếu KPI hoặc thiếu Traffic; do đó `status = partial` phải được hiển thị cùng giá trị tổng hợp để người xem nhận biết mức độ thiếu dữ liệu.

## 10. Thứ tự triển khai đề xuất

1. **Backend (An), xong 19/11:** chạy file SQL trên CSDL thử; kiểm tra tạo bảng, trigger, index và View; kiểm tra liên kết province/ward/cell.
2. **Data/QA:** nạp GeoJSON 34 tỉnh và 168 phường/xã TP.HCM; nạp danh sách cell; tạo dữ liệu KPI mô phỏng theo từng cell/giờ; điền phương pháp, giả định, seed và giới hạn trong `data_sources`.
3. **An + Data/QA:** kiểm tra kết quả tổng hợp theo giờ/ngày, trường hợp Traffic bằng 0, thiếu KPI, thiếu Traffic và vùng partial.
4. **Backend:** API đọc từ `mv_region_kpi` / `mv_region_kpi_daily`; sau khi nạp dữ liệu và ngưỡng, refresh hai MV và chạy `ANALYZE`.
5. **Frontend:** dùng `region_code`, `cell_code`, `kpi_code`, `period_start`/`local_date`, `status`, `quality_level`, `data_nature` để hiển thị bản đồ và nhãn “Dữ liệu mô phỏng”.
6. **Leader:** đối chiếu kết quả với yêu cầu Mentor, theo dõi các điểm cần xác nhận từ KPI dictionary và cập nhật tài liệu.

## 11. Câu lệnh tham khảo

Chạy trên database đã có quyền tạo extension PostGIS:

```bash
psql -d <database_name> -v ON_ERROR_STOP=1 -f N4.6_Database_Schema.sql
```

Truy vấn KPI CSSR cấp tỉnh theo một giờ:

```sql
SELECT region_code, region_name, value, cells_reported, cells_total,
       status, aggregation_status, traffic_weight_gb, updated_at
FROM n46.mv_region_kpi
WHERE region_level = 'province'
  AND kpi_code = 'cssr'
  AND period_start = TIMESTAMPTZ '2026-10-01 08:00:00+07';
```

Truy vấn KPI User Throughput cấp phường theo ngày:

```sql
SELECT region_code, region_name, local_date, value,
       cell_hours_reported, cell_hours_expected, status
FROM n46.mv_region_kpi_daily
WHERE region_level = 'ward'
  AND kpi_code = 'user_throughput'
  AND local_date = DATE '2026-10-01';
```

Kiểm tra ngưỡng KPI:

```sql
SELECT * FROM n46.v_kpi_threshold_check;
```

Kiểm tra vùng `partial` vẫn có phân loại sau khi đã nạp đầy đủ ngưỡng:

```sql
SELECT COUNT(*) AS partial_without_quality
FROM n46.mv_region_kpi
WHERE status = 'partial'
  AND value IS NOT NULL
  AND is_quality_kpi IS TRUE
  AND quality_level IS NULL;
-- Kỳ vọng: 0, khi mọi KPI chất lượng đã có ngưỡng phủ giá trị.
```

---

## Tệp đi kèm

- `N4.6_Database_Schema.sql`: script tạo schema, bảng, ràng buộc, trigger, index, 3 View gốc và 2 Materialized View, 4 KPI và nguồn mô phỏng mẫu.
- `N4.6_Refresh_Materialized_Views.sql`: script chạy sau khi nạp dữ liệu để refresh hai Materialized View và cập nhật thống kê bằng `ANALYZE`.
- Script schema chưa nạp GeoJSON, danh sách cell hoặc giá trị KPI giả; các phần này do Backend/Data/QA thực hiện sau khi cấu trúc được rà soát.



## 12. Quy ước triển khai

- Schema PostgreSQL có tên cố định `n46`; số phiên bản chỉ nằm trong tài liệu và tên file SQL `N4.6_Database_Schema.sql`.
- Điều kiện JOIN ngưỡng trong cả hai view gốc là `a.value IS NOT NULL`; vùng `partial` có giá trị KPI vẫn được phân loại, nhưng `status` vẫn là `partial`.
- Hai view gốc `v_region_kpi` và `v_region_kpi_daily` là nguồn logic để đối chiếu. Hai Materialized View `mv_region_kpi` và `mv_region_kpi_daily` là nguồn đọc cho API sau khi refresh.
- Hai MV được tạo `WITH DATA` khi cài Schema. Sau khi nạp xong GeoJSON, cells, cell KPI và ngưỡng, phải chạy lại hai lệnh `REFRESH MATERIALIZED VIEW` rồi `ANALYZE`; refresh không tự động.
- Index MV: `(kpi_code, region_level, period_start)` và `(region_code, kpi_code, period_start)` cho dữ liệu giờ; tương tự thay `period_start` bằng `local_date` cho dữ liệu ngày.
- View giữ `status` và `aggregation_status`. API trả `status` là `ok`, `partial` hoặc `missing`; khi `aggregation_status = 'no_positive_traffic'`, API trả `value = NULL` và `reason = 'no_positive_traffic'`.
- RAT cho phép `4G` và `5G`, mặc định `4G`; giai đoạn 1 chỉ nạp `4G`.
- Cell thuộc tỉnh đã nạp phường/xã bắt buộc có `ward_id`; trigger kiểm tra phường thuộc đúng tỉnh. Nạp tỉnh và phường trước khi nạp cell.
- Trước khi chạy trên môi trường đã có schema `n46`, Backend cần backup và đối chiếu các object hiện hữu. `CREATE TABLE IF NOT EXISTS` không tự migrate cấu trúc bảng cũ.

Chạy SQL trên database có quyền tạo PostGIS và `btree_gist`:

```bash
psql -d <database_name> -v ON_ERROR_STOP=1 -f N4.6_Database_Schema.sql
```

Sau khi đã nạp xong ranh giới, danh sách cell, dữ liệu KPI và ngưỡng, chạy:

```sql
REFRESH MATERIALIZED VIEW n46.mv_region_kpi;
REFRESH MATERIALIZED VIEW n46.mv_region_kpi_daily;
ANALYZE n46.mv_region_kpi;
ANALYZE n46.mv_region_kpi_daily;
```

Kiểm tra ví dụ từ Materialized View:

```sql
SELECT region_code, region_name, value, status, quality_level, threshold_type
FROM n46.mv_region_kpi
WHERE kpi_code = 'cssr'
  AND region_level = 'province'
  AND period_start = TIMESTAMPTZ '2026-10-01 08:00:00+07';
```
