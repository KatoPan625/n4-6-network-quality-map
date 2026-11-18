# Dữ liệu và KPI N4.6

Cập nhật: 18/11/2026. Thiết kế chi tiết của CSDL ở [SCHEMA-V2.1.md](SCHEMA-V2.1.md); SQL ở `db/N4.6_Database_Schema_V2.1.sql`. Tài liệu này tóm tắt quy tắc dữ liệu cho người sinh, nhập và đọc dữ liệu.

## Hiện trạng

| Nguồn (`source_code`) | Loại | Mặc định | Nội dung | Người phụ trách |
| --- | --- | --- | --- | --- |
| `SIM-V1` | Mô phỏng | Có | Bộ dữ liệu chính: 165 ô × 8 KPI × 26 tuần (~34.000 dòng). **Chưa có**; phương pháp, giả định đang để trống chờ điền | Vũ |
| `BE-SAMPLE` | Mô phỏng | Không | Dữ liệu thử của Backend: 165 ô × 8 KPI × 2 tuần (19/10 và 26/10/2026), giá trị ngẫu nhiên. Chỉ để test API, không dùng cho bản đồ hay báo cáo | An |

Chưa có dữ liệu thật hay dữ liệu công khai. VNPT NET khả năng cao không cung cấp KPI; thầy cho phép dùng dữ liệu mô phỏng hoặc công khai (email 17/11).

## Quy tắc nguồn dữ liệu

- Mỗi giá trị KPI thuộc đúng một nguồn trong bảng `data_sources`.
- Mỗi nguồn phải mô tả: loại nguồn, tính chất (`real`/`simulated`), phạm vi không gian và thời gian, phương pháp thu thập/sinh, phiên bản script, seed, giả định, giới hạn.
- Nguồn loại `simulation` bắt buộc `data_nature = simulated`; CSDL chặn trường hợp ngược lại.
- Bản đồ, API và báo cáo luôn hiện nhãn **"Dữ liệu mô phỏng"** khi `data_nature = simulated`. Không dùng dữ liệu mô phỏng để kết luận về chất lượng mạng thực tế của VNPT.
- Không đưa dữ liệu thật, tọa độ trạm, thông tin thuê bao vào repo. Dữ liệu chưa được phép chia sẻ để trong `data/raw/` hoặc `data/private/` (đã bị `.gitignore`).

## Đơn vị không gian và thời gian

- **Ô lưới:** vuông 1 km, mã `G1K-<i>-<j>`. `i`, `j` là chỉ số của `ST_SquareGrid` trong EPSG:32648, nên mã ô không đổi khi mở rộng khung. 165 ô: `i` từ 683 đến 697, `j` từ 1190 đến 1200. Ô nguyên vẹn, không cắt theo ranh giới.
- **Tuần:** thứ Hai – Chủ nhật, xác định bằng `period_start` (thứ Hai). 26 tuần từ 04/05/2026 đến 01/11/2026. Không tổng hợp lên tháng, vì trung vị của tuần không gộp lên tháng được.

## Cách tính và tổng hợp KPI

| Nhóm KPI | Giá trị của một ô trong một tuần | Cột cần có |
| --- | --- | --- |
| Throughput (Mbps), latency, jitter (ms) | Trung vị các phép đo hợp lệ trong tuần | `value`, `sample_count` |
| Tỉ lệ (%): packet loss, availability, 2 KPI HTTP | Tổng tử số trong tuần / tổng mẫu số trong tuần × 100 | `value`, `numerator_value`, `denominator_value`, `sample_count` |

- KPI tỉ lệ phải có tử số và mẫu số, `0 ≤ tử ≤ mẫu`, `mẫu > 0`, và `value = tử / mẫu × 100` (sai lệch tối đa 0,0001). CSDL kiểm bằng trigger.
- Giá trị phải nằm trong miền hợp lệ của KPI (`valid_min`, `valid_max` trong bảng `kpis`); tỉ lệ từ 0 đến 100.
- Chỉ so sánh hai tuần của cùng KPI, cùng nguồn.

## Thiếu dữ liệu, dữ liệu sai và giá trị 0

| `status` | `value` | Ý nghĩa |
| --- | --- | --- |
| `ok` | Có số, `sample_count > 0` | Đo/sinh được. `0` là giá trị thật, ví dụ 0% mất gói |
| `missing` | `null` | Không có dữ liệu cho ô và tuần đó |
| `invalid` | `null` | Có dữ liệu nhưng bị loại; bắt buộc ghi lý do ở `quality_note` |

- Không bao giờ thay dữ liệu thiếu bằng `0`.
- Ô không có dòng nào trong CSDL cũng được API trả là `missing`.
- `quality_level` để `null` khi `status` khác `ok` hoặc KPI chưa có ngưỡng.

## Ngưỡng tốt / trung bình / kém

- Lưu trong bảng `kpi_thresholds`, khoảng nửa mở `[min, max)`; mỗi KPI đủ 3 mức, không chồng lấn, không hở, đúng chiều tốt/kém. Kiểm tra bằng `SELECT * FROM v_kpi_threshold_check;`.
- Mỗi ngưỡng phải ghi căn cứ (`threshold_basis`). Ngưỡng lấy từ quy chuẩn ghi `standard` và tên tài liệu; ngưỡng nhóm tự đề xuất ghi `team_proposed`, không gọi là chuẩn hay ngưỡng của VNPT.
- Căn cứ ưu tiên: QCVN 34:2022/BTTTT (thay QCVN 34:2019/BTTTT), ITU-T Y.1540. Hiện **chưa có số**.

## Định dạng file nhập

File CSV UTF-8, một dòng là một KPI của một ô trong một tuần. Mẫu: `backend/data/sample_kpi.csv`.

| Cột | Bắt buộc | Ghi chú |
| --- | --- | --- |
| `source_code` | Có | Ví dụ `SIM-V1`; nguồn phải có sẵn trong `data_sources` |
| `region_code` | Có | Ví dụ `G1K-685-1191` |
| `kpi_code` | Có | Một trong 8 mã KPI |
| `period_start` | Có | `YYYY-MM-DD`, phải là thứ Hai, nằm trong khoảng của nguồn |
| `value` | Khi `status = ok` | Để trống khi `missing`/`invalid` |
| `status` | Có | `ok`, `missing`, `invalid` |
| `sample_count` | Có | Số nguyên ≥ 0; > 0 khi `ok` |
| `numerator_value`, `denominator_value` | Với KPI tỉ lệ | Để trống với KPI không phải tỉ lệ |
| `quality_note` | Khi `invalid` | Lý do loại |

Mỗi bộ (`source_code`, `kpi_code`, `period_start`, `region_code`) chỉ có một dòng. Nạp lại thì cập nhật dòng cũ, không tạo bản trùng. CSDL chặn dòng sai và báo lý do. Chức năng nhập file qua API (`POST /api/v1/imports`) dự kiến làm ở tuần 12.

## Yêu cầu với bộ mô phỏng `SIM-V1`

- Tái lập được: cùng script, cùng seed (`random_seed` trong `data_sources`) cho cùng kết quả.
- Có cả ô tốt, trung bình, kém; có ô và tuần thiếu dữ liệu, có vài dòng `invalid` để thử luồng hiển thị.
- Ghi giả định thật sự áp dụng. Ví dụ: khung có một đoạn sông Sài Gòn, các ô chủ yếu là mặt nước nên có ít mẫu hơn.
- Điền `collection_method`, `assumptions`, `limitations` trước khi dùng cho báo cáo.
