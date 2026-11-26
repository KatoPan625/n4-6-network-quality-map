# N4.6 — Frontend (Bản đồ chất lượng mạng 4G)

Giao diện bản đồ web tương tác (React + Vite + Leaflet + Chart.js) hiển thị các chỉ số KPI chất lượng mạng di động 4G theo 34 tỉnh/thành phố và 168 phường/xã TP.HCM.

## Yêu cầu

- Node.js 18+ (hoặc 20+) và npm
- Backend FastAPI chạy tại `http://localhost:8000` (xem hướng dẫn ở `../backend/README.md`)

## Cài đặt & Chạy local

```powershell
cd frontend
npm install
npm run dev
```

Mở trình duyệt tại `http://localhost:5173`. Vite đã cấu hình proxy `/api` sang `http://localhost:8000`.

## Kiểm tra mã nguồn

```powershell
npm run lint    # Kiểm tra Oxlint (0 errors, 0 warnings)
npm run build   # Build bản production vào thư mục dist/
```
