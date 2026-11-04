# Kế hoạch triển khai N4.6

Cập nhật: 04/11/2026. Trạng thái: **đề xuất nội bộ, chưa được mentor xác nhận**.

Nhóm có 5 thành viên mới làm quen; chưa xác định kỹ năng, thời gian khả dụng, dữ liệu thật hoặc công nghệ. TV1–TV5 là ký hiệu tạm, không phải phân vai đã được các thành viên nhận. Lịch dưới đây dùng các mốc nhóm cung cấp; nhóm xác nhận lịch họp và bàn giao cụ thể với mentor/PM.

## Việc làm ngay

1. Chủ repo mời thành viên vào GitHub; từng người xác nhận truy cập được và điền tên, username, phần muốn học, thời gian có thể dành mỗi tuần vào bảng phân công.
2. Cả nhóm đọc [yêu cầu](REQUIREMENTS.md), ghi rõ điểm chưa hiểu và phần đang chờ mentor.
3. Mỗi người nhận một việc thử có đầu ra trong bảng dưới. Chọn một người điều phối tạm thời.
4. Người điều phối tổng hợp câu hỏi và trao đổi với mentor về phạm vi, dữ liệu, KPI và nghiệm thu; lưu kết quả bằng biên bản.
5. Tập trung minh chứng tại issue/PR hoặc tài liệu được liên kết; cập nhật báo cáo theo [mẫu chung](REPORT-TEMPLATE.md).

## Phân công thử: 04–06/11/2026

| Vai trò tạm | Tên / GitHub | Công việc | Đầu ra để cả nhóm kiểm tra |
| --- | --- | --- | --- |
| TV1 — yêu cầu, điều phối; sau này tham gia tích hợp/demo | Chưa điền | Đối chiếu mô tả đề tài, đề xuất phạm vi, tổng hợp câu hỏi mentor | Phạm vi 1–2 trang; danh sách chức năng và điểm cần xác nhận |
| TV2 — dữ liệu và KPI | Chưa điền | Khảo sát 2–4 KPI ứng viên, đơn vị/cách tính, nguồn dữ liệu và phương án mô phỏng | Bảng KPI có nguồn tham khảo; cấu trúc dữ liệu mẫu đề xuất và hạn chế |
| TV3 — lưu trữ và xử lý dữ liệu | Chưa điền | Phác mô hình vùng–thời gian–KPI, xác định dữ liệu cần cho từng chức năng | Sơ đồ dữ liệu và danh sách API sơ bộ; chưa cần lập trình |
| TV4 — bản đồ và tương tác | Chưa điền | Phác bản đồ, bộ lọc, chú giải, thao tác chọn vùng, trạng thái thiếu dữ liệu | Bản phác màn hình và luồng sử dụng có chú thích |
| TV5 — chi tiết KPI, báo cáo và kiểm thử | Chưa điền | Phác xem chi tiết/so sánh, nội dung xuất báo cáo; liệt kê tình huống kiểm thử | Bản phác chi tiết KPI và bảng kiểm thử ban đầu |

Mỗi người tự ghi tài liệu và kiểm thử phần mình. TV5 tổng hợp cách kiểm thử chung, không gánh toàn bộ báo cáo. Khi lập trình, cả 5 người cần có phần kỹ thuật và minh chứng cá nhân rõ ràng.

## Chốt kế hoạch trước 14/11

| Thời gian | Công việc | Kết quả kiểm tra |
| --- | --- | --- |
| 07/11 | Mỗi người trình bày kết quả, vướng mắc và nguyện vọng; xem chéo đầu ra | Điều chỉnh vai trò theo kết quả và thời gian khả dụng; ghi người chính/người kiểm tra |
| 08–10/11 | Ghép yêu cầu, dữ liệu, mô hình và giao diện | Các phần thống nhất mã vùng, KPI, đơn vị, thời gian; liệt kê các khác biệt còn mở |
| 11–12/11 | Chia việc đến mốc báo cáo 28/11 | Mỗi việc có người phụ trách, hạn, sản phẩm, tiêu chí hoàn thành và phụ thuộc |
| 13–14/11 | Gửi mentor rà soát; cập nhật theo phản hồi | Nhóm thống nhất bản kế hoạch; các nội dung chưa được mentor trả lời vẫn ghi “chờ xác nhận” |

Nếu mentor chưa phản hồi, tiếp tục khảo sát và chuẩn bị dữ liệu mô phỏng theo mô tả đề tài; ghi nhãn mô phỏng, không dùng để kết luận chất lượng mạng thực tế. Không coi việc mentor chưa trả lời là đồng ý phạm vi hoặc tiêu chí nghiệm thu.

## Đầu ra đến báo cáo 28/11

| Người phụ trách sau khi chốt | Đầu ra |
| --- | --- |
| TV1 | Tài liệu yêu cầu/phạm vi, biên bản trao đổi, tiến độ, rủi ro và điểm cần mentor quyết định |
| TV2 | Khảo sát nguồn dữ liệu, định nghĩa KPI, dữ liệu mẫu được phép sử dụng và hạn chế |
| TV3 | Mô hình dữ liệu, cách nhập/xử lý và API sơ bộ để đánh giá tính khả thi |
| TV4 | Luồng sử dụng và phác bản đồ đối chiếu với yêu cầu |
| TV5 | Phác chi tiết/so sánh, tiêu chí kiểm thử và đề xuất cách đánh giá kết quả |

Cả nhóm làm rõ “phương pháp cơ sở để so sánh” với mentor trước báo cáo 28/11. Khi có dữ liệu mẫu, mới đề xuất quy mô kiểm thử và chỉ tiêu định lượng; không tự đặt ngưỡng chất lượng mạng để thay yêu cầu mentor.

## Mốc toàn dự án

| Thời gian | Mốc / sản phẩm |
| --- | --- |
| 26–30/10/2026 | Đăng ký đề tài, lập nhóm, chọn trưởng nhóm; mốc đã qua theo lịch, kiểm tra hồ sơ thực tế |
| 01–14/11/2026 | Chốt vai trò, phạm vi, phân công và kế hoạch |
| 22–28/11/2026 — tuần 4 | Phân tích yêu cầu, khảo sát dữ liệu, phương pháp cơ sở; báo cáo tháng 28/11 |
| 06–12/12/2026 — tuần 6 | Hoàn thành thiết kế giải pháp |
| 20–26/12/2026 — tuần 8 | Prototype; báo cáo tháng 26/12 |
| 27/12/2026–02/01/2027 — tuần 9 | Giữa kỳ và đánh giá chéo phân tích/thiết kế |
| 17–23/01/2027 — tuần 12 | Phát triển, kiểm thử; báo cáo tháng 23/01 |
| 31/01–13/02/2027 — tuần 14–15 | Tài liệu dự kiến trùng nghỉ Tết; nhóm thống nhất lịch làm việc với PM |
| 14–20/02/2027 — tuần 16 | Sản phẩm gần hoàn chỉnh; báo cáo tháng 20/02 |
| 21–27/02/2027 — tuần 17 | Trình bày, demo, nhận góp ý; bắt đầu đánh giá chéo cuối kỳ |
| 28/02–06/03/2027 — tuần 18 | Nghiệm thu, bàn giao, hoàn tất đánh giá chéo |

Các giai đoạn sau 28/11 chỉ là mốc định hướng; chia task cụ thể sau khi có dữ liệu và thiết kế được thống nhất. Mỗi mốc cần mã nguồn/tài liệu, kết quả kiểm tra và minh chứng đóng góp tương ứng.

## Theo dõi công việc — đề xuất GitHub Projects

**Chưa tạo board.** Đề xuất dùng issue làm đầu việc, Projects làm bảng theo dõi; GitHub hỗ trợ bảng/board/roadmap và trường ngày tùy chỉnh ([tài liệu chính thức](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)).

- Trạng thái: Chưa làm → Đang làm → Chờ kiểm tra → Hoàn thành; dùng Bị chặn khi chưa thể tiếp tục.
- Mỗi việc có một người phụ trách chính, hạn, mức ưu tiên, mốc báo cáo, người kiểm tra, checklist và link minh chứng. Người hỗ trợ ghi trong nội dung issue.
- Người thực hiện cập nhật tiến độ trong ngày làm việc; nếu bị chặn, ghi nguyên nhân và người cần hỗ trợ.
- Chuyển “Hoàn thành” khi có đầu ra, tiêu chí được kiểm tra và người kiểm tra xác nhận. Hoàn thành nội bộ không thay cho nghiệm thu của mentor.
- Theo dõi số việc đã được kiểm tra trên tổng số việc của mốc; không dùng số issue, commit hoặc phần trăm checklist để tự chấm năng lực cá nhân vì khối lượng việc khác nhau.
- Trường hạn dùng để xem/sắp xếp theo ngày; kế hoạch này chưa thiết lập hay cam kết nhắc hạn tự động.
- Khi có board, cập nhật trạng thái và deadline tại issue/Projects; tài liệu này giữ mốc và quy tắc để tránh hai nơi ghi khác nhau.

## Nhịp phối hợp và lưu minh chứng

Mỗi thành viên có Daily Report mỗi ngày làm việc. Người điều phối tổng hợp báo cáo nhóm, biên bản và hồ sơ để PM truy cập được. Theo quy trình dự án: gửi lịch báo cáo cho PM ít nhất 3 ngày làm việc trước buổi; nộp báo cáo tuần trong 1 ngày làm việc sau buổi báo cáo. Giờ họp cụ thể do nhóm thống nhất với PM.

Lưu các quyết định, thay đổi phạm vi, báo cáo định kỳ, kết quả kiểm thử/demo và đóng góp cá nhân từ đầu. Tài liệu gốc tham chiếu: mô tả N4.6, Quy_trinh_HKDN_UTH_VNPT_NET_v2 và lịch nhóm đã cung cấp; không đưa tài liệu/dữ liệu nội bộ chưa được phép lên repo.
