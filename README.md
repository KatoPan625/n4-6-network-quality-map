# N4.6 — Bản đồ số hiển thị chất lượng mạng theo khu vực

Dự án học kỳ doanh nghiệp UTH – VNPT NET. Nhóm xây dựng bản đồ web hiển thị KPI chất lượng **mạng cố định** (Internet cáp quang) đã tổng hợp theo ô lưới và theo tuần. Bản đồ hỗ trợ lọc, xem chi tiết, so sánh và xuất báo cáo.


## Phạm vi đã chốt

| Mục | Nội dung |
| --- | --- |
| Loại mạng | Cố định (Internet cáp quang). Không dùng RSRP, SINR hay KPI mạng di động khác |
| KPI (8) | `download_throughput`, `upload_throughput`, `latency`, `jitter`, `packet_loss_rate`, `network_availability`, `http_ip_access_failure_ratio`, `http_dropped_sessions_ratio` |
| Không gian | Lưới vuông 1 km, khung `HCM-CENTER-NE` 15 × 11 km (khu Bến Thành đến Thủ Đức cũ), 165 ô mã `G1K-<i>-<j>` |
| Thời gian | Tuần thứ Hai – Chủ nhật, 26 tuần từ 04/05/2026 đến 01/11/2026; không tổng hợp lên tháng |
| Dữ liệu | Mô phỏng, luôn gắn nhãn `simulated`; |
| Mức chất lượng | Tốt / trung bình / kém. Chưa có số; mỗi ngưỡng phải dẫn căn cứ (QCVN 34:2022/BTTTT, ITU-T Y.1540…). Ngưỡng nhóm tự đề xuất ghi `team_proposed` |

## Nhóm

| Thành viên | Vai trò |
| --- | --- |
| Đạt | Trưởng nhóm; yêu cầu, schema CSDL, liên lạc mentor |
| An (`KatoPan625`) | Backend & API |
| Đức | Frontend bản đồ |
| Vũ | Dữ liệu mô phỏng, kiểm thử (Data/QA) |

## Cấu trúc repo

| Thư mục | Nội dung |
| --- | --- |
| `backend/` | FastAPI + PostgreSQL 17/PostGIS 3.5.2. Hướng dẫn chạy: [backend/README.md](backend/README.md); hợp đồng API: [backend/docs/api-contract.md](backend/docs/api-contract.md) |
| `db/` | SQL schema chính thức V2.1 |
| `docs/` | Thiết kế CSDL (Schema V2.1) và mẫu báo cáo dùng chung |
| `frontend/` | Chưa có (Đức) |
| `data/` | Chưa có (Vũ). `data/raw/`, `data/private/`, `data/generated/` không được commit |

## Bảo mật dữ liệu

Giữ repo riêng tư. Không commit `.env`, mật khẩu, token, tọa độ trạm hay dữ liệu thuê bao. API và bản đồ chỉ dùng số liệu tổng hợp theo ô. Quyền công bố mã nguồn và giấy phép cần nhóm và mentor thống nhất trước khi công khai.
