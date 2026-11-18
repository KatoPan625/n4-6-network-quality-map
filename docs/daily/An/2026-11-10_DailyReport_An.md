# Daily Report — 10/11/2026

- **Ngày:** 10/11/2026 (Thứ Ba)
- **Thành viên / GitHub:** Lại Hồ Phước An / KatoPan625 — Backend & API
- **Issue đang thực hiện:** Chưa có issue (repo chung chưa tạo). Việc theo kế hoạch tuần 1–2: cài môi trường backend/CSDL, phác API và dữ liệu đầu vào/đầu ra.
- **Kết quả đã làm hôm nay và link minh chứng:**
  - Cài công cụ: DBeaver, Bruno, QGIS LTR, image `postgis/postgis:17-3.5`.
  - Dựng sandbox backend FastAPI + PostgreSQL 17/PostGIS 3.5.2 bằng Docker Compose; schema nháp 3 bảng `region`, `kpi_definition`, `kpi_value`.
  - Viết 7 API đọc: `/health`, `/health/db`, `/api/v1/kpis`, `/api/v1/regions` (GeoJSON), `/api/v1/kpi-values`, `/api/v1/regions/{code}/kpis`, `/api/v1/compare`. Quy ước thiếu dữ liệu trả `null` + `status: "missing"`, tách biệt với giá trị 0.
  - Tạo dữ liệu thử (lưới 3×3 giả lập, 2 KPI, 2 kỳ); viết bản nháp hợp đồng API và xuất `openapi.json`.
  - Kiểm thử: 15/15 test pytest pass, 8/8 request Bruno pass; baseline quy mô lab p95 < 6 ms (dữ liệu thử, không phải chỉ tiêu nghiệm thu).
  - Minh chứng: `backend/evidence/2026-11-10_*.png` (luồng CSDL → API, JSON thiếu dữ liệu, Swagger, pytest, Bruno, baseline, git log); `backend/docs/api-contract.md`; commit `f8e875c`, `cecb7ea`, `363da76`.
- **Việc chưa xong / vướng mắc / người cần hỗ trợ:** Chưa có repo chung (cần Đạt). KPI, cách tính, ngưỡng và mức chi tiết vùng chờ mentor. Định dạng file nhập cần thống nhất với Vũ.
- **Việc tiếp theo và hạn dự kiến:** Gửi `docs/api-contract.md` cho Đạt và Đức góp ý trước buổi thống nhất tuần 3.
- **Thay đổi deadline hoặc phạm vi cần trao đổi:** API `compare` thuộc kế hoạch tuần 10–11 nhưng đã làm sớm trên dữ liệu thử; cần kiểm tra lại sau khi chốt KPI.
