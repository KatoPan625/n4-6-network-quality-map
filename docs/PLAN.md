# Kế hoạch triển khai N4.6

Cập nhật: 18/11/2026 (tuần 3). Bản 04/11 dùng vai trò tạm TV1–TV5; nay thay bằng phân công thực tế. Thầy chưa xác nhận hướng đã chốt ngày 18/11.

## Phân công

| Thành viên | Vai trò | Phụ trách chính |
| --- | --- | --- |
| Đạt | Trưởng nhóm | Yêu cầu, schema CSDL, liên lạc mentor, tổng hợp báo cáo nhóm |
| An (`KatoPan625`) | Đồng trưởng nhóm, Backend & API | CSDL PostGIS, API, hợp đồng API, kiểm thử Backend |
| Đức | Frontend | Bản đồ, bộ lọc, chú giải, màn hình chi tiết và so sánh |
| Vũ | Data/QA | Sinh dữ liệu mô phỏng, mô tả phương pháp, kiểm thử dữ liệu |

Ngưỡng chất lượng do An và Vũ cùng tra. Mỗi người tự viết tài liệu, kiểm thử và lưu minh chứng cho phần mình.

## Đã xong đến 18/11

- Repo chung, nhật ký quyết định, schema V2.1 (`db/`, `docs/SCHEMA-V2.1.md`).
- Chốt mạng cố định, 8 KPI, lưới 1 km, khung 165 ô, chu kỳ tuần, dữ liệu mô phỏng.
- Backend chạy trên schema V2.1: 7 API đọc, dữ liệu thử `BE-SAMPLE`, 19 test, 8 request Bruno, API contract v0.2. Đang ở PR #1, chờ review.

## Việc đang mở (tuần 3)

| # | Việc | Người làm | Hạn | Đầu ra |
| --- | --- | --- | --- | --- |
| 1 | Duyệt PR #1 (Backend V2.1, schema, tài liệu) | Đạt | 20/11 | PR được review và hợp nhất |
| 2 | Tra ngưỡng 3 mức (QCVN 34:2022/BTTTT, ITU-T Y.1540), nạp `kpi_thresholds`, chạy `v_kpi_threshold_check` | An + Vũ | 20/11 | Bảng ngưỡng có căn cứ; view kiểm tra trả `ok` cho 8 KPI |
| 3 | Script sinh dữ liệu 165 ô × 8 KPI × 26 tuần (~34.000 dòng); điền phương pháp, giả định vào `SIM-V1` | Vũ | Chốt ở họp 21/11 | Script tái lập được (seed cố định), file CSV theo định dạng ở `DATA.md` |
| 4 | Gửi Đức `api-contract.md`, `openapi.json`, JSON mẫu; Đức chọn Leaflet hay MapLibre | An, Đức | 21/11 | Quyết định thư viện ghi vào DECISIONS.md |
| 5 | Họp chốt hợp đồng API | Cả nhóm | 21/11 | Biên bản, API contract v1.0 |
| 6 | Email thầy xác nhận hướng đã chốt; lưu ảnh email 17/11 vào `docs/mentor/` | Đạt | Tuần 3 | Email và ảnh lưu trong repo |
| 7 | Mời thành viên vào repo; bật bảo vệ nhánh `main` | Chủ repo (An) | Tuần 3 | Mọi người push được nhánh riêng; `main` yêu cầu PR |
| 8 | Đối chiếu số bảng, số mục ETSI TS 103 222-2 trước khi trích vào báo cáo | Vũ | Trước 28/11 | Trích dẫn đúng trong báo cáo |

## Đến báo cáo tháng 28/11 (tuần 4)

| Người | Đầu ra |
| --- | --- |
| Đạt | Tài liệu yêu cầu và phạm vi, biên bản các buổi họp, rủi ro, câu hỏi cho mentor |
| An | API contract v1.0, Backend chạy với `SIM-V1` và ngưỡng, kết quả test |
| Đức | Phác giao diện bản đồ, chú giải, màn hình chi tiết; khung dự án Frontend |
| Vũ | Bộ `SIM-V1` và mô tả phương pháp, giả định, giới hạn |

## Mốc toàn dự án

| Thời gian | Mốc / sản phẩm |
| --- | --- |
| 01–14/11/2026 | Chốt vai trò, phạm vi, phân công (xong) |
| 15–21/11/2026 — tuần 3 | Chốt API, schema, KPI, đơn vị, xử lý dữ liệu thiếu; họp chốt API 21/11 |
| 22–28/11/2026 — tuần 4 | Phân tích yêu cầu, dữ liệu, phương pháp cơ sở; báo cáo tháng 28/11 |
| 06–12/12/2026 — tuần 6 | Hoàn thành thiết kế giải pháp |
| 20–26/12/2026 — tuần 8 | Prototype; báo cáo tháng 26/12 |
| 27/12/2026 – 02/01/2027 — tuần 9 | Giữa kỳ, đánh giá chéo phân tích/thiết kế |
| 03–23/01/2027 — đến tuần 12 | Phát triển, kiểm thử; nhập/xuất dữ liệu (`POST /imports`, `GET /exports`); báo cáo tháng 23/01 |
| 31/01 – 13/02/2027 — tuần 14–15 | Dự kiến trùng nghỉ Tết; thống nhất lịch với PM |
| 14–20/02/2027 — tuần 16 | Sản phẩm gần hoàn chỉnh; báo cáo tháng 20/02 |
| 21–27/02/2027 — tuần 17 | Trình bày, demo, nhận góp ý; bắt đầu đánh giá chéo cuối kỳ |
| 28/02 – 06/03/2027 — tuần 18 | Nghiệm thu, bàn giao, hoàn tất đánh giá chéo |

## Theo dõi công việc

- Mỗi đầu việc là một issue (mẫu `.github/ISSUE_TEMPLATE/task.md`) có người phụ trách, người kiểm tra, hạn và tiêu chí hoàn thành.
- Trạng thái: Chưa làm → Đang làm → Chờ kiểm tra → Hoàn thành; dùng Bị chặn khi phải chờ người khác, ghi rõ chờ ai.
- Chỉ chuyển Hoàn thành khi có đầu ra, đã kiểm tra và người kiểm tra xác nhận. Hoàn thành nội bộ không thay cho nghiệm thu của mentor.
- Chưa tạo GitHub Projects. Nếu tạo, trạng thái và hạn ghi ở issue/Projects; tài liệu này chỉ giữ mốc.

## Nhịp phối hợp và minh chứng

- Mỗi người có Daily Report mỗi ngày làm việc trong `docs/daily/<tên>/YYYY-MM-DD_DailyReport_<tên>.md`, theo [mẫu](REPORT-TEMPLATE.md).
- Đạt tổng hợp báo cáo nhóm, biên bản và hồ sơ cho PM.
- Theo quy trình chương trình: gửi lịch báo cáo cho PM ít nhất 3 ngày làm việc trước buổi; nộp báo cáo tuần trong 1 ngày làm việc sau buổi.
- Quyết định mới ghi vào [DECISIONS.md](DECISIONS.md) kèm ngày, lý do, người chốt.
