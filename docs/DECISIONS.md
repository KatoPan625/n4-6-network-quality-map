# Nhật ký quyết định N4.6

Ghi các quyết định đã chốt, theo thứ tự thời gian. Quyết định sau thay thế quyết định trước nếu mâu thuẫn. Các tài liệu `README.md`, `docs/REQUIREMENTS.md`, `docs/PLAN.md`, `docs/DATA.md` đã cập nhật theo nhật ký này ngày 18/11; nếu còn mâu thuẫn, nhật ký này được ưu tiên.

## Đang có hiệu lực

| Ngày | Quyết định | Lý do | Người chốt |
|----|----|----|----|
| 10/11 | CSDL PostgreSQL 17 + PostGIS 3.5.2, SRID 4326; Backend FastAPI | Cần truy vấn không gian (lưới, GeoJSON) ngay trong CSDL; PostGIS là chuẩn phổ biến | An (Backend), Đạt xác nhận 17/11 |
| 10/11 | Thiếu dữ liệu trả `value: null` + `status: "missing"`, không dùng 0 | Tránh hiểu nhầm "0 Mbps" là đo được 0 | An |
| 10/11 | Không lưu, không trả tọa độ trạm hay thuê bao; chỉ dữ liệu tổng hợp theo vùng | Bảo mật dữ liệu nhà mạng và khách hàng | An |
| 17/11 | Được dùng dữ liệu mô phỏng hoặc công khai; phải mô tả nguồn, phương pháp, giả định, giới hạn và tách rõ thật/mô phỏng | Hướng dẫn của thầy qua email 17/11; VNPT NET khả năng cao không cung cấp KPI | Thầy |
| 17/11 | Khoảng 8–10 KPI; phân loại tốt/trung bình/kém có căn cứ ITU, 3GPP, quy chuẩn Việt Nam | Hướng dẫn của thầy. Khác mô tả đề tài gốc (2–4 KPI), cần ghi vào biên bản tuần 3 | Thầy |
| 18/11 | Mạng **cố định** (Internet cáp quang) | RSRP/SINR mô phỏng khó bảo vệ; mạng cố định gọn phạm vi và có quy chuẩn Việt Nam rõ (QCVN 34:2022/BTTTT) | Đạt đề xuất, nhóm đồng ý |
| 18/11 | 8 KPI: download, upload, latency, jitter, packet loss rate, network availability, HTTP IP-service access failure ratio, HTTP dropped sessions ratio | 6 KPI chung của truy cập Internet, cộng 2 KPI HTTP có trong ETSI TS 103 222-2 cho Internet tốc độ cao | Đạt (Schema V2) |
| 18/11 | Lưới vuông 1 km; mã ô từ `i, j` của `ST_SquareGrid` trong EPSG:32648; ô nguyên vẹn, không cắt biên | Dễ thiết kế và giải thích; mã ô ổn định; diện tích các ô bằng nhau nên so sánh công bằng | Đạt (V2), An sửa (V2.1) |
| 18/11 | Khung nghiên cứu `HCM-CENTER-NE`: 15 × 11 km, từ khu Bến Thành về phía Thủ Đức cũ, 165 ô | Có cả lõi đô thị và vùng ven; đủ lớn để bản đồ có ý nghĩa, nhẹ cho Frontend | An và Đạt |
| 18/11 | Chu kỳ tuần (thứ Hai – Chủ nhật), 26 tuần từ 04/05/2026 đến 01/11/2026; không tổng hợp lên tháng | 26 điểm mỗi ô đủ vẽ xu hướng; giá trị trung vị của tuần không gộp lên tháng được | Đạt (V2), An và Đạt chốt ngày |
| 18/11 | Dùng dữ liệu mô phỏng, gắn nhãn `simulated` trong CSDL, API, bản đồ và báo cáo | Chưa có dữ liệu VNPT; theo hướng dẫn của thầy | Đạt (V2) |
| 18/11 | Backend dùng thẳng file `db/N4.6_Database_Schema_V2.1.sql` khi tạo CSDL; bỏ schema nháp 3 bảng | Một nguồn schema duy nhất, tránh lệch giữa Backend và tài liệu | An |
| 18/11 | Dữ liệu thử của Backend nằm trong nguồn riêng `BE-SAMPLE` (`is_default = FALSE`), không ghi vào `SIM-V1` | Không trộn dữ liệu test với bộ mô phỏng chính thức của Vũ | An |
| 18/11 | Schema V2.1: 6 bảng (`study_areas`, `regions`, `kpis`, `kpi_thresholds`, `data_sources`, `kpi_values`) và 2 view | Sửa 12 lỗi của V2, xem mục 0 trong `docs/SCHEMA-V2.1.md` | An đề xuất; An và Đạt chốt khung, 26 tuần, bảng `study_areas`; chờ Đạt duyệt qua PR |

## Đã bỏ

| Ngày bỏ | Phương án | Lý do bỏ |
|----|----|----|
| 18/11 | Mạng di động 4G/5G với RSRP, SINR (chọn ngày 17/11) | Chuyển sang mạng cố định |
| 18/11 | Accessibility Rate, Retainability Rate | KPI kiểu 3GPP cho mạng di động, không hợp với FTTH |
| 18/11 | Tỷ lệ đạt tốc độ cam kết, tỷ lệ sự cố trên 100 thuê bao | Hai KPI HTTP theo ETSI có căn cứ rõ hơn |
| 18/11 | Chu kỳ tháng; tổng hợp tuần lên tháng | Quá ít điểm dữ liệu; trung vị không cộng dồn được |
| 18/11 | Cắt ô biên theo ranh giới | Ô nhỏ hơn 1 km² so sánh không công bằng |
| 18/11 | Viện dẫn QCVN 34:2019/BTTTT | Đã bị thay bằng QCVN 34:2022/BTTTT |

## Chưa chốt

- Số ngưỡng tốt/trung bình/kém của 8 KPI (An và Vũ, hạn 20/11).
- Phương pháp và tham số sinh dữ liệu mô phỏng (Vũ).
- Thư viện bản đồ: Leaflet hay MapLibre (Đức).
- Hợp đồng API v0.2 (`backend/docs/api-contract.md`): đổi khóa `code` → `kpi_code`, thêm `source`, `data_nature`, `quality_level`; chốt ở họp 21/11.
- Thầy chưa xác nhận hướng đã chốt ngày 18/11.
