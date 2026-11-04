# Yêu cầu đề tài N4.6

Tài liệu khởi đầu cho **Xây dựng bản đồ số hiển thị chất lượng mạng theo khu vực**. Mục tiêu là trình bày KPI mạng tổng hợp theo không gian và thời gian để hỗ trợ so sánh khu vực.

## Trạng thái và căn cứ

- Căn cứ phạm vi: mục N4.6 trong tài liệu mô tả đề tài UTH – VNPT NET do nhóm cung cấp.
- Các yêu cầu có nhãn **Phạm vi tài liệu** được rút từ mô tả đó; chưa có xác nhận rằng mentor đã chốt toàn bộ yêu cầu triển khai.
- Các cách kiểm tra dưới đây là **đề xuất nghiệm thu**, cần thống nhất với mentor sau khi khảo sát dữ liệu.
- Chưa chốt công nghệ, nguồn dữ liệu, KPI cụ thể, địa lý, chu kỳ tổng hợp và người sử dụng.
- Hiện chưa có sản phẩm triển khai hay bộ dữ liệu để tuyên bố các yêu cầu đã đạt.

## Phạm vi tài liệu

- Bản đồ web theo vùng hành chính tổng quát hoặc ô lưới giả lập.
- Chọn 2–4 KPI mẫu, chẳng hạn khả dụng, độ trễ, mất gói hoặc thông lượng.
- Dùng dữ liệu tổng hợp theo vùng hoặc mô phỏng; thử nghiệm ở quy mô lab.
- Có bộ lọc, chú giải, thể hiện dữ liệu thiếu, so sánh thời gian và báo cáo tổng hợp.
- Không cần hiển thị vị trí trạm nhạy cảm.

## Yêu cầu chức năng

| Mã | Yêu cầu — phạm vi tài liệu | Cách kiểm tra đề xuất |
| --- | --- | --- |
| FR-01 | Thiết kế mô hình dữ liệu không gian, KPI và API. | Có tài liệu liên kết vùng, thời gian và KPI; mô tả đầu vào/đầu ra API, đơn vị và dữ liệu mẫu; các thành phần dùng cùng mã vùng. |
| FR-02 | Hiển thị lớp chất lượng trên bản đồ tương tác. | Với bộ dữ liệu đối chiếu, vùng và giá trị hiển thị đúng; thao tác phóng to, thu nhỏ và xem vùng hoạt động. |
| FR-03 | Lọc theo thời gian, khu vực và loại KPI. | Kiểm tra từng bộ lọc và tổ hợp bộ lọc; kết quả khớp dữ liệu đối chiếu, kể cả trường hợp không có bản ghi. |
| FR-04 | Có chú giải, màu sắc và trạng thái dữ liệu thiếu. | Màu khớp quy tắc đã thống nhất; chú giải có đơn vị; vùng thiếu dữ liệu được phân biệt với giá trị bằng 0. |
| FR-05 | Có màn hình chi tiết KPI. | Người xem xác định được vùng, kỳ dữ liệu, giá trị, đơn vị và thời gian cập nhật của KPI đang xem. |
| FR-06 | So sánh chất lượng theo thời gian. | Chọn hai kỳ có thể so sánh; kết quả khớp phép tính đối chiếu đã ghi trong tài liệu; thông báo khi thiếu dữ liệu hoặc hai kỳ không tương thích. |
| FR-07 | Xuất báo cáo tổng hợp. | Báo cáo ghi phạm vi lọc, kỳ dữ liệu, KPI và đơn vị; số liệu khớp kết quả đối chiếu theo phương pháp tổng hợp được thống nhất. |
| FR-08 | Có dữ liệu demo và hướng dẫn nhập dữ liệu. | Thành viên khác làm theo hướng dẫn để nhập bộ mẫu; bản ghi không hợp lệ được nhận diện và có thông tin để xử lý. |

## Yêu cầu chất lượng

| Mã | Yêu cầu | Cách kiểm tra đề xuất |
| --- | --- | --- |
| NFR-01 | **Phạm vi tài liệu:** không lộ tọa độ trạm/thuê bao hoặc vùng nhạy cảm chưa được duyệt. | Rà soát dữ liệu, phản hồi API, giao diện, bản xuất và mã nguồn trước demo/bàn giao; chỉ sử dụng dữ liệu được phép chia sẻ. |
| NFR-02 | **Phạm vi tài liệu:** mỗi KPI có đơn vị, cách tính, chú giải và thời gian cập nhật rõ ràng. | Đối chiếu định nghĩa KPI với dữ liệu và giao diện; phân biệt kỳ đo với thời điểm nhập/cập nhật. |
| NFR-03 | **Phạm vi tài liệu:** bản đồ nền và ranh giới được cấp phép. | Có nguồn và điều kiện sử dụng; ghi công theo yêu cầu của từng nguồn. |
| NFR-04 | **Phạm vi tài liệu:** kiểm thử thao tác và hiệu năng ở quy mô lab. | Ghi máy thử, số vùng/bản ghi, thao tác và thời gian đo; thống nhất ngưỡng đạt sau baseline, chưa đặt số tùy ý. |
| NFR-05 | **Đề xuất:** có thể tái lập kết quả demo. | Người khác làm theo hướng dẫn để chạy sản phẩm và thực hiện kịch bản kiểm thử với cùng bộ mẫu. |

## Sản phẩm bàn giao theo mô tả

- Thiết kế dữ liệu và API; bản đồ web tương tác và màn hình chi tiết KPI.
- Bộ dữ liệu demo, hướng dẫn nhập và kiểm thử.
- Báo cáo độ phân giải không gian, tính cập nhật và hạn chế của bản đồ.
- Hồ sơ chương trình: mã nguồn/hướng dẫn chạy, phân tích và thiết kế, kết quả kiểm thử/demo, báo cáo, slide và bảng đóng góp cá nhân.

## Những quyết định cần mentor xác nhận

- Người dùng, nhu cầu phân tích và chức năng ưu tiên.
- Khu vực, loại vùng, 2–4 KPI, định nghĩa/cách tính và chu kỳ dữ liệu.
- Nguồn dữ liệu được phép dùng; phương án mô phỏng khi dữ liệu thật chưa có.
- Căn cứ ngưỡng màu/chất lượng, cách so sánh và tổng hợp; không tự gán mức tốt/xấu cho mạng thực tế.
- Định dạng xuất, quy mô lab, baseline, tiêu chí hiệu năng và môi trường triển khai.

**Giới hạn đề xuất, chờ xác nhận:** chưa đưa thu thập phép đo trên điện thoại, dự báo AI hoặc cập nhật thời gian thực vào kế hoạch đầu tiên.
