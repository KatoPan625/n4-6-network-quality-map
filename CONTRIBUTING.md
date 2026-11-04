# Cách làm việc nhóm

## Nhận việc

- Mỗi issue có một người phụ trách chính, một người kiểm tra, hạn, kết quả cần nộp và tiêu chí hoàn thành.
- TV1–TV5 là ký hiệu tạm, không phải tài khoản GitHub. Chủ repo sẽ mời thành viên; nhóm tự thống nhất người nhận từng mảng.
- Chia việc đủ nhỏ để có thể nộp và kiểm tra độc lập. Báo ngay khi thiếu dữ liệu hoặc cần quyết định, ghi rõ ai có thể gỡ vướng.

## Thay đổi tài liệu và mã nguồn

1. Đọc yêu cầu liên quan và issue trước khi sửa.
2. Tạo nhánh theo đầu việc, ví dụ `docs/12-khao-sat-kpi` hoặc `feat/25-bo-loc`. Nhánh do Codex tạo dùng tiền tố `codex/`.
3. Chỉ sửa phần thuộc đầu việc; tránh cùng sửa một tệp nếu chưa phối hợp.
4. Mở pull request (PR), liên kết issue, mô tả thay đổi và cách kiểm tra.
5. Nhờ một thành viên khác review; sửa góp ý rồi hợp nhất vào `main`.

Đây là quy ước nhóm, chưa phải quy tắc bảo vệ nhánh được bật trên GitHub. Khi chọn công nghệ, bổ sung hướng dẫn chạy và các lệnh kiểm thử phù hợp.

## Khi nào được đánh dấu hoàn thành?

- Đã nộp đúng sản phẩm và đáp ứng tiêu chí trong issue.
- Có link minh chứng: tài liệu, PR, dữ liệu demo được phép chia sẻ hoặc kết quả kiểm thử.
- Người kiểm tra đã xác nhận; nếu có thay đổi mã nguồn, PR liên quan đã được hợp nhất.
- Các hạn chế và câu hỏi chưa xử lý được ghi rõ. Không ghi đã được mentor duyệt nếu chưa có phản hồi.

Mỗi người kiểm thử và viết tài liệu phần mình. Thành viên phụ trách tổng hợp không chịu trách nhiệm viết thay toàn bộ nhóm.

## Theo dõi và minh chứng

- Cập nhật Daily Report trong mỗi ngày làm việc, theo [mẫu](docs/REPORT-TEMPLATE.md).
- Lưu biên bản họp, quyết định, báo cáo và link sản phẩm ở nơi nhóm/PM có quyền truy cập.
- Lịch báo cáo gửi PM ít nhất 3 ngày làm việc trước buổi báo cáo; báo cáo tuần nộp trong 1 ngày làm việc sau buổi, theo quy trình được cung cấp.
- Phần trăm checklist chỉ mô tả tiến độ các mục đã chia, không tự đánh giá chất lượng. Không xếp hạng đóng góp chỉ bằng số commit hoặc số issue.

## Bảo vệ dữ liệu

Không commit tệp `.env`, mật khẩu/token hoặc dữ liệu hạn chế chia sẻ. Các thư mục `data/raw/`, `data/private/` và `data/generated/` được bỏ qua mặc định. Kiểm tra quyền sử dụng trước khi đưa bất kỳ dữ liệu nào khác vào repo; `.gitignore` không thay thế việc kiểm tra nội dung.
