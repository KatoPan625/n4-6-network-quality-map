# Daily Report — 17/11/2026

- **Ngày:** 17/11/2026 (Thứ Ba)
- **Thành viên / GitHub:** Lại Hồ Phước An / KatoPan625 — Backend & API (đồng trưởng nhóm cùng Đạt)
- **Issue đang thực hiện:** Chưa có issue. Thống nhất dữ liệu, KPI và schema theo kế hoạch tuần 3.
- **Kết quả đã làm hôm nay và link minh chứng:**
  - Nhận định hướng của thầy: VNPT NET khả năng cao không cung cấp KPI; nhóm được dùng dữ liệu mô phỏng hoặc công khai, phải mô tả đầy đủ nguồn và tách rõ thật/mô phỏng; chọn khoảng 8–10 KPI; phân loại tốt/trung bình/kém có cơ sở ITU, 3GPP, quy chuẩn; không gian theo phường/xã hoặc ô lưới 500 m/1 km; chu kỳ tuần hoặc tháng trong 3–6 tháng. Minh chứng: email của thầy ngày 17/11 (cần lưu ảnh/email vào hồ sơ nhóm).
  - Xác nhận công nghệ CSDL cho Lead: PostgreSQL 17 + PostGIS 3.5.2, SRID 4326 (đang chạy trong sandbox Backend).
  - Đề xuất 8 KPI cho mạng di động: download/upload throughput, latency, jitter, packet loss, RSRP, SINR, network availability — trạng thái: đề xuất, chờ nhóm thống nhất.
  - Góp ý bản nháp schema v1 của Đạt (`N4.6_Database_Schema_Draft_v1`): đề xuất thêm bảng `kpi_thresholds`, `data_sources`; thêm `region_code`, `kpi_code`, `higher_is_better`, `kpi_group`; đổi `period TIMESTAMP` thành `period_type` + `period_start`; thêm `status`, ràng buộc UNIQUE chống trùng, `updated_at`, index; khai báo `geom geometry(MultiPolygon, 4326) NOT NULL` kèm index GiST.
- **Việc chưa xong / vướng mắc / người cần hỗ trợ:** Cần cả nhóm chốt: mạng di động hay cố định, danh sách KPI (Vũ xác nhận mô phỏng được), khu vực và kích thước ô lưới, chu kỳ dữ liệu. Mô tả đề tài ghi 2–4 KPI, thầy hướng dẫn 8–10 KPI — cần ghi nhận khi chốt. Repo chung vẫn chưa có.
- **Việc tiếp theo và hạn dự kiến:** Họp nhóm chốt 4 quyết định trên; sau khi Đạt chốt schema v2, cập nhật sandbox Backend (thêm `kpi_thresholds`, `data_sources`, sinh lưới bằng `ST_SquareGrid`) — hạn 21/11.
- **Thay đổi deadline hoặc phạm vi cần trao đổi:** Số KPI tăng từ 2–4 (mô tả đề tài) lên 8–10 (hướng dẫn của thầy) làm tăng khối lượng phần dữ liệu; cần cân đối lại phân việc.
