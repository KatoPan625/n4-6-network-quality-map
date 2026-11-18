# Yêu cầu đề tài N4.6

**Xây dựng bản đồ số hiển thị chất lượng mạng theo khu vực.** Mục tiêu: trình bày KPI chất lượng mạng cố định, tổng hợp theo không gian và thời gian, để so sánh các khu vực.

Cập nhật: 18/11/2026. Các quyết định trong tài liệu này lấy từ [DECISIONS.md](DECISIONS.md); khi mâu thuẫn, DECISIONS.md được ưu tiên.

## Căn cứ

- Mục N4.6 trong tài liệu mô tả đề tài UTH – VNPT NET.
- Email hướng dẫn của thầy ngày 17/11/2026: được dùng dữ liệu mô phỏng hoặc công khai; khoảng 8–10 KPI; phân loại tốt/trung bình/kém có căn cứ ITU, 3GPP, quy chuẩn Việt Nam; không gian theo phường/xã hoặc lưới 500 m/1 km; chu kỳ tuần hoặc tháng trong 3–6 tháng.
- Quyết định của nhóm ngày 18/11/2026. Thầy chưa xác nhận các quyết định này.

Các cách kiểm tra dưới đây là **đề xuất nghiệm thu**, cần thống nhất với mentor.

## Phạm vi

| Mục | Mô tả đề tài gốc | Đã chốt (18/11) |
| --- | --- | --- |
| Loại mạng | Không nêu | Mạng cố định (Internet cáp quang) |
| KPI | 2–4 KPI mẫu | 8 KPI, theo hướng dẫn của thầy (xem bảng dưới) |
| Không gian | Vùng hành chính tổng quát hoặc ô lưới giả lập | Lưới vuông 1 km, khung `HCM-CENTER-NE` 15 × 11 km, 165 ô |
| Thời gian | Không nêu | Tuần thứ Hai – Chủ nhật, 26 tuần (04/05/2026 – 01/11/2026) |
| Dữ liệu | Tổng hợp theo vùng hoặc mô phỏng; quy mô lab | Mô phỏng, gắn nhãn `simulated` |
| Bảo mật | Không hiển thị vị trí trạm nhạy cảm | Không lưu, không trả tọa độ trạm hay thuê bao |

Phương án dự phòng nếu lưới 1 km không phù hợp: lưới 500 m hoặc phường/xã (schema đã hỗ trợ `grid_500m` và `ward`).

### 8 KPI

| Mã | Tên | Đơn vị | Cao là tốt | Căn cứ định nghĩa |
| --- | --- | --- | --- | --- |
| `download_throughput` | Download Throughput | Mbps | Có | ITU-T Y.1540; QCVN 34:2022/BTTTT |
| `upload_throughput` | Upload Throughput | Mbps | Có | ITU-T Y.1540; QCVN 34:2022/BTTTT |
| `latency` | Latency (RTT) | ms | Không | ITU-T Y.1540 (IPTD) |
| `jitter` | Jitter | ms | Không | ITU-T Y.1540 (IPDV) |
| `packet_loss_rate` | Packet Loss Rate | % | Không | ITU-T Y.1540 (IPLR) |
| `network_availability` | Network Availability | % | Có | ITU-T Y.1540 |
| `http_ip_access_failure_ratio` | HTTP IP-Service Access Failure Ratio | % | Không | ETSI TS 103 222-2 V1.3.1 |
| `http_dropped_sessions_ratio` | HTTP Dropped Sessions Ratio | % | Không | ETSI TS 103 222-2 V1.3.1 |

Cách tính và cách tổng hợp theo tuần ở [SCHEMA-V2.1.md](SCHEMA-V2.1.md).

## Yêu cầu chức năng

| Mã | Yêu cầu | Cách kiểm tra đề xuất | Trạng thái 18/11 |
| --- | --- | --- | --- |
| FR-01 | Thiết kế mô hình dữ liệu không gian, KPI và API. | Có tài liệu liên kết ô, tuần, KPI và nguồn; API mô tả đầu vào/đầu ra, đơn vị và JSON mẫu; mọi thành phần dùng chung `region_code`, `kpi_code`, `source_code`. | Schema V2.1 và API contract v0.2 có bản nháp, chốt 21/11 |
| FR-02 | Hiển thị lớp chất lượng trên bản đồ tương tác. | Với bộ dữ liệu đối chiếu, 165 ô và giá trị hiển thị đúng; phóng to, thu nhỏ, chọn ô hoạt động. | Chưa làm (Frontend) |
| FR-03 | Lọc theo tuần, khu vực và KPI. | Kiểm tra từng bộ lọc và tổ hợp; kết quả khớp dữ liệu đối chiếu, kể cả khi không có bản ghi. | API có; giao diện chưa làm |
| FR-04 | Chú giải, màu theo mức tốt/trung bình/kém và trạng thái thiếu dữ liệu. | Màu khớp ngưỡng trong `kpi_thresholds`; chú giải có đơn vị và căn cứ ngưỡng; ô thiếu dữ liệu khác ô có giá trị 0; ngưỡng `team_proposed` được ghi rõ. | Chưa có số ngưỡng |
| FR-05 | Màn hình chi tiết KPI của một ô. | Người xem thấy ô, tuần, giá trị, đơn vị, số mẫu, mức chất lượng và nguồn dữ liệu. | API có; giao diện chưa làm |
| FR-06 | So sánh chất lượng giữa hai tuần. | Chênh lệch `B − A` khớp phép tính đối chiếu; báo rõ khi một tuần thiếu dữ liệu. | API có; giao diện chưa làm |
| FR-07 | Xuất báo cáo tổng hợp. | Báo cáo ghi bộ lọc, tuần, KPI, đơn vị, nguồn và nhãn "Dữ liệu mô phỏng"; số liệu khớp kết quả đối chiếu. | Dự kiến tuần 12 |
| FR-08 | Dữ liệu demo và hướng dẫn nhập dữ liệu. | Thành viên khác nhập được bộ mẫu theo hướng dẫn; bản ghi sai bị chặn kèm lý do. | Có dữ liệu thử của Backend; bộ `SIM-V1` chưa có |

## Yêu cầu chất lượng

| Mã | Yêu cầu | Cách kiểm tra đề xuất |
| --- | --- | --- |
| NFR-01 | Không lộ tọa độ trạm, thuê bao hoặc vùng nhạy cảm. | Rà soát dữ liệu, phản hồi API, giao diện, bản xuất và mã nguồn trước demo/bàn giao. |
| NFR-02 | Mỗi KPI có đơn vị, cách tính, cách tổng hợp, căn cứ và kỳ dữ liệu rõ ràng. | Đối chiếu bảng `kpis` với giao diện và báo cáo. |
| NFR-03 | Dữ liệu mô phỏng luôn có nhãn và mô tả phương pháp. | Mọi phản hồi API có `data_nature`; bản đồ và báo cáo hiện nhãn "Dữ liệu mô phỏng"; `data_sources` có đủ phương pháp, giả định, giới hạn. |
| NFR-04 | Bản đồ nền và ranh giới được cấp phép. | Có nguồn và điều kiện sử dụng; ghi công theo yêu cầu từng nguồn. |
| NFR-05 | Kiểm thử thao tác và hiệu năng ở quy mô lab. | Ghi máy thử, số ô/bản ghi, thao tác và thời gian đo. Chỉ đặt ngưỡng đạt sau khi có baseline. |
| NFR-06 | Tái lập được kết quả demo. | Người khác chạy lại sản phẩm theo hướng dẫn với cùng bộ dữ liệu (seed cố định). |

## Sản phẩm bàn giao

- Thiết kế dữ liệu và API; bản đồ web tương tác và màn hình chi tiết KPI.
- Bộ dữ liệu mô phỏng, hướng dẫn nhập và kiểm thử.
- Báo cáo về độ phân giải không gian, tính cập nhật và hạn chế của bản đồ.
- Hồ sơ chương trình: mã nguồn và hướng dẫn chạy, phân tích – thiết kế, kết quả kiểm thử/demo, báo cáo, slide, bảng đóng góp cá nhân.

## Còn mở

- Số ngưỡng tốt/trung bình/kém của 8 KPI (An và Vũ).
- Phương pháp và tham số sinh dữ liệu mô phỏng (Vũ).
- Thư viện bản đồ: Leaflet hay MapLibre (Đức).
- Định dạng xuất báo cáo, baseline hiệu năng, môi trường demo.
- Thầy xác nhận các quyết định ngày 18/11.

Ngoài phạm vi kế hoạch hiện tại: đo trên điện thoại, dự báo bằng AI, cập nhật thời gian thực.
