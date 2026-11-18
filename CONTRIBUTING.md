# Cách làm việc nhóm

## Nhận việc

- Mỗi issue có một người phụ trách chính, một người kiểm tra, hạn, kết quả cần nộp và tiêu chí hoàn thành.
- Phân công theo mảng: Đạt (trưởng nhóm, schema), An (Backend & API), Đức (Frontend), Vũ (Data/QA).
- Chia việc đủ nhỏ để có thể nộp và kiểm tra độc lập. Báo ngay khi thiếu dữ liệu hoặc cần quyết định, ghi rõ ai có thể gỡ vướng.

## Thay đổi tài liệu và mã nguồn

1. Đọc yêu cầu liên quan và issue trước khi sửa.
2. Tạo nhánh theo đầu việc từ `main`, ví dụ `docs/12-khao-sat-kpi` hoặc `feat/25-bo-loc`. Không push thẳng `main`.
3. Chỉ sửa phần thuộc đầu việc; tránh cùng sửa một tệp nếu chưa phối hợp.
4. Mở pull request (PR), liên kết issue, mô tả thay đổi và cách kiểm tra.
5. Nhờ một thành viên khác review; sửa góp ý rồi hợp nhất vào `main`.

Đây là quy ước nhóm; bảo vệ nhánh `main` trên GitHub chưa bật.

Khi đổi KPI, đơn vị, ngưỡng hay API, cập nhật `docs/SCHEMA-V2.1.md` hoặc `backend/docs/api-contract.md` trong cùng PR.

## Kiểm tra trước khi mở PR

- **Backend** (trong `backend/`, cần CSDL đang chạy và đã nạp dữ liệu thử): `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`. Đổi API thì cập nhật `docs/api-contract.md` và chạy lại `scripts/export_openapi.py`.
- **Schema** (`db/`): chạy lại toàn bộ file SQL trên CSDL trống với `-v ON_ERROR_STOP=1`.
- **Frontend, dữ liệu:** bổ sung lệnh kiểm tra khi có mã nguồn.
- Ghi tệp văn bản bằng UTF-8 không BOM (Bruno không đọc được BOM).

## Khi nào được đánh dấu hoàn thành?

- Đã nộp đúng sản phẩm và đáp ứng tiêu chí trong issue.
- Có link minh chứng: tài liệu, PR, dữ liệu demo được phép chia sẻ hoặc kết quả kiểm thử.
- Người kiểm tra đã xác nhận; nếu có thay đổi mã nguồn, PR liên quan đã được hợp nhất.
- Các hạn chế và câu hỏi chưa xử lý được ghi rõ. Không ghi đã được mentor duyệt nếu chưa có phản hồi.

Mỗi người kiểm thử và viết tài liệu phần mình. Thành viên phụ trách tổng hợp không chịu trách nhiệm viết thay toàn bộ nhóm.

## Theo dõi và minh chứng

- Cập nhật Daily Report trong mỗi ngày làm việc theo [mẫu](docs/REPORT-TEMPLATE.md); lưu ở nơi nhóm/PM truy cập được, không cần đưa vào repo.
- Lưu biên bản họp, quyết định, báo cáo và link sản phẩm ở nơi nhóm/PM có quyền truy cập.
- Lịch báo cáo gửi PM ít nhất 3 ngày làm việc trước buổi báo cáo; báo cáo tuần nộp trong 1 ngày làm việc sau buổi, theo quy trình được cung cấp.
- Phần trăm checklist chỉ mô tả tiến độ các mục đã chia, không tự đánh giá chất lượng. Không xếp hạng đóng góp chỉ bằng số commit hoặc số issue.

## Bảo vệ dữ liệu

Không commit tệp `.env`, mật khẩu/token hoặc dữ liệu hạn chế chia sẻ. Các thư mục `data/raw/`, `data/private/` và `data/generated/` được bỏ qua mặc định. Kiểm tra quyền sử dụng trước khi đưa bất kỳ dữ liệu nào khác vào repo; `.gitignore` không thay thế việc kiểm tra nội dung.
