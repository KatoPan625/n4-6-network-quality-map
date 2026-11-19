# N4.6 — Bản đồ số hiển thị chất lượng mạng theo khu vực

Dự án học kỳ doanh nghiệp UTH – VNPT NET. Nhóm xây dựng bản đồ web hiển thị KPI chất lượng **mạng di động 4G**, tính ở cấp cell rồi tổng hợp lên tỉnh/thành và phường/xã, theo giờ và theo ngày. Người dùng là nhân viên kỹ thuật giám sát hệ thống. Bản đồ hỗ trợ lọc, xem chi tiết, so sánh và xuất báo cáo.


## Phạm vi đã chốt

| Mục | Nội dung |
| --- | --- |
| Loại mạng | Di động 4G (theo hướng dẫn của mentor VNPT NET); cột `rat` cho phép mở rộng 5G |
| KPI (4) | `cssr`, `service_drop_all`, `user_throughput` (Mbps, tải xuống), `traffic` (GB). Định nghĩa và căn cứ 3GPP TS 32.450 ở [docs/SCHEMA.md](docs/SCHEMA.md) |
| Tổng hợp | Cell → vùng: `Σ(KPI × traffic) / Σtraffic`; riêng `traffic` cộng tổng. Vùng thiếu một phần cell có trạng thái `partial` |
| Không gian | 34 tỉnh/thành sau sắp xếp 01/07/2025; chi tiết phường/xã cho TP.HCM (168 đơn vị). Không lưu, không hiển thị tọa độ trạm/cell |
| Thời gian | Theo giờ, 30 ngày (01–30/10/2026), giờ Việt Nam; cấp ngày tính từ giờ |
| Dữ liệu | Mô phỏng, luôn gắn nhãn `simulated`; **không phải số liệu của VNPT** |
| Mức chất lượng | Tốt / trung bình / kém. Chưa có số; ngưỡng nhóm tự đề xuất ghi `team_proposed`, không gọi là chuẩn |
| Ranh giới | sapnhap.bando.com.vn (Bộ NN&MT), bản trích xuất `myleo198/sapnhap-bando-vn`, CC BY-NC 4.0 |

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
| `db/` | SQL schema chính thức và script refresh materialized view |
| `docs/` | Thiết kế CSDL ([SCHEMA.md](docs/SCHEMA.md)) và mẫu báo cáo dùng chung |
| `frontend/` | Chưa có (Đức) |
| `data/` | Chưa có (Vũ). `data/raw/`, `data/private/`, `data/generated/` không được commit |

## Bảo mật dữ liệu

Giữ repo riêng tư. Không commit `.env`, mật khẩu, token, tọa độ trạm hay dữ liệu thuê bao. API và bản đồ chỉ dùng số liệu tổng hợp theo tỉnh/phường. Quyền công bố mã nguồn và giấy phép cần nhóm và mentor thống nhất trước khi công khai.
