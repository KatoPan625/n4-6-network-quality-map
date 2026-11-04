# Chuẩn bị dữ liệu N4.6

Hướng dẫn khảo sát dữ liệu để triển khai bản đồ KPI theo vùng. **Đây là đề xuất ban đầu, chưa phải schema hoặc hợp đồng API đã chốt.** Chưa có bộ dữ liệu thật hay mô phỏng trong kho mã nguồn.

## Nguồn và quyền sử dụng

Ưu tiên dữ liệu đã tổng hợp theo vùng và thời gian được mentor cho phép sử dụng. Dữ liệu công khai hoặc mô phỏng là phương án cần xác nhận nếu chưa nhận được dữ liệu phù hợp.

Với mỗi nguồn, ghi lại:

- Tên nguồn, đường dẫn hoặc đơn vị cung cấp, ngày truy cập/nhận và phiên bản.
- Phạm vi địa lý/thời gian, phương pháp đo, KPI và chu kỳ cập nhật.
- Giấy phép hoặc văn bản cho phép; quyền lưu trữ, sửa đổi, công bố, demo và phân phối lại.
- Yêu cầu ghi công, hạn chế bảo mật, thời hạn lưu và người được truy cập.
- Nguồn/giấy phép của bản đồ nền và ranh giới, kiểm tra riêng với dữ liệu KPI.

Không coi dữ liệu xem được trên website là dữ liệu được phép tải và phát hành lại. Không đưa dữ liệu thật, tọa độ nhạy cảm, thông tin thuê bao hoặc thông tin truy cập dịch vụ vào kho mã nguồn khi chưa được phép.

## Trường dữ liệu ứng viên

Tên trường chỉ để trao đổi; sẽ điều chỉnh theo nguồn và thiết kế được thống nhất. Một bản ghi KPI dự kiến biểu diễn **một chỉ số của một vùng trong một kỳ dữ liệu**.

| Thành phần | Trường ứng viên | Nội dung cần làm rõ |
| --- | --- | --- |
| Vùng | `region_id`, `region_name` | Mã ổn định để nối KPI với hình học; loại vùng và phiên bản ranh giới. |
| Hình học vùng | `region_id`, `geometry` | Polygon/ô lưới được phép sử dụng; định dạng và hệ tọa độ phải được ghi rõ. |
| Kỳ dữ liệu | `period_start`, `period_end` | Múi giờ, chu kỳ và quy ước tính các mốc biên. |
| Chỉ số | `kpi_code`, `value`, `unit` | Định nghĩa, đơn vị, cách tính và ý nghĩa giá trị hợp lệ. |
| Độ đầy đủ | `sample_count`, `data_status` | Số mẫu nếu có; lý do thiếu hoặc không đủ điều kiện công bố. |
| Nguồn | `source`, `is_synthetic` | Nguồn đo hay mô phỏng; không trộn mà không nhận diện được. |
| Cập nhật | `updated_at` | Thời điểm cập nhật bản ghi, phân biệt với thời gian đo. |

Nếu nguồn phân theo nhà cung cấp hoặc công nghệ mạng, phải giữ thông tin phân nhóm cần thiết; chỉ thêm bộ lọc tương ứng khi phạm vi đã được chốt.

## Định nghĩa KPI và tổng hợp

- Mỗi KPI cần tên, đơn vị, cách tính, chu kỳ, cách tổng hợp theo vùng/thời gian và hạn chế đo.
- Tỷ lệ cần biết mẫu số; chỉ số trung bình cần biết số mẫu/trọng số nếu muốn tổng hợp lại.
- Không lấy trung bình các giá trị trung bình một cách máy móc. Chọn phép tổng hợp theo định nghĩa và thông tin nguồn; nếu thiếu trọng số, ghi rõ hạn chế hoặc chưa tổng hợp.
- Các vùng và kỳ chỉ được so sánh khi tương thích về định nghĩa KPI, đơn vị, cách đo, độ dài kỳ và phạm vi không gian. Thay đổi ranh giới phải có quy tắc đối chiếu.
- Khi đổi đơn vị, giữ quy tắc chuyển đổi và kiểm tra bằng ví dụ đối chiếu. Không cộng/trộn các đơn vị khác nhau.
- Chưa đặt ngưỡng phân loại chất lượng mạng. Cần căn cứ của mentor/nguồn; ngưỡng minh họa phải ghi rõ là phục vụ demo.

## Thiếu dữ liệu và giá trị bằng 0

- `0` chỉ dùng khi đó là giá trị có ý nghĩa hợp lệ của KPI.
- Thiếu bản ghi hoặc không đo được phải có trạng thái rõ; không thay tự động bằng `0`.
- Bản đồ, chi tiết và báo cáo phải phân biệt không có dữ liệu, giá trị bằng 0 và dữ liệu bị loại theo quy tắc đã thống nhất.
- Nếu nguồn không cung cấp số mẫu hoặc lý do thiếu, ghi là không có thông tin; không tự suy diễn.

## Kiểm tra trước khi nhập

- Trường bắt buộc, kiểu dữ liệu, đơn vị và giá trị hợp lệ theo định nghĩa KPI.
- Mã vùng tồn tại và nối đúng với hình học; hình học/hệ tọa độ phù hợp.
- Thời gian hợp lệ, cùng quy ước múi giờ; phát hiện kỳ chồng lấn hoặc không đầy đủ.
- Phát hiện bản ghi trùng theo khóa đã thống nhất, gồm các chiều phân nhóm của nguồn; không âm thầm ghi đè.
- Ghi nhận bản ghi bị từ chối và lý do, tránh bỏ dữ liệu mà người nhập không biết.

## Bộ mẫu và minh chứng cần chuẩn bị

Sau khi chốt quy ước, tạo bộ mẫu nhỏ có kết quả đối chiếu tính được: nhiều vùng, ít nhất hai kỳ có thể so sánh, giá trị 0 hợp lệ, vùng thiếu dữ liệu và bản ghi lỗi để thử luồng nhập.

Dữ liệu mô phỏng phải tái tạo được theo hướng dẫn, gắn nhãn rõ trên demo/báo cáo và không dùng để kết luận chất lượng mạng thực tế. Quy mô mẫu, khu vực, KPI và phương pháp tạo hiện chưa được chốt.

Lưu mô tả nguồn/quyền sử dụng, từ điển dữ liệu, quy tắc làm sạch/tổng hợp, kết quả kiểm tra và hướng dẫn nhập cùng phiên bản bộ dữ liệu. Dữ liệu hạn chế truy cập lưu tại nơi được phê duyệt, không đính vào minh chứng công khai.
