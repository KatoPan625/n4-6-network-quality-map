# Daily Report — 13/11/2026

- **Ngày:** 13/11/2026 (Thứ Sáu)
- **Thành viên / GitHub:** Lại Hồ Phước An / KatoPan625 — Backend & API
- **Issue đang thực hiện:** Chưa có issue. Duy trì môi trường backend.
- **Kết quả đã làm hôm nay và link minh chứng:** Dữ liệu Docker bị xóa nhầm (image, container, volume CSDL). Đã khôi phục: tải lại image PostGIS, tạo lại container và volume, schema tự khởi tạo từ `db/init/`, nạp lại dữ liệu thử bằng `scripts/load_sample.py`. Chạy lại test: 15/15 pass. Mã nguồn và tài liệu (ổ D) không bị ảnh hưởng.
- **Việc chưa xong / vướng mắc / người cần hỗ trợ:** Vẫn chờ repo chung và phản hồi của mentor.
- **Việc tiếp theo và hạn dự kiến:** Bổ sung hướng dẫn sao lưu CSDL (`pg_dump`) vào README trước khi nhóm dùng dữ liệu cần giữ.
- **Thay đổi deadline hoặc phạm vi cần trao đổi:** Không.
