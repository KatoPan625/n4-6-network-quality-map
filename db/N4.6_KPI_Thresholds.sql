-- N4.6 - Nguong tot / trung binh / kem cho 3 KPI chat luong (de xuat cua nhom).
--
-- Trang thai: Dat da duyet 20/11. threshold_type = 'team_proposed' (khong phai nguong chuan chinh thuc).
-- Chay sau db/N4.6_Database_Schema.sql, roi refresh MV:
--   psql -1 -f db/N4.6_KPI_Thresholds.sql      (-1: chay trong 1 giao dich)
--   psql -f db/N4.6_Refresh_Materialized_Views.sql
-- Chay lai nhieu lan khong loi (xoa nguong team_proposed cu cua 3 KPI roi nap lai).
--
-- Vi sao la team_proposed, khong phai standard:
--   QCVN do chat luong dich vu dau cuoi (goi thu / tai thu), tren toan mang hoac mot vung,
--   it nhat 3.000 cuoc goi. Du an tinh KPI mang theo cell/gio (E-RAB). Dinh nghia khac nhau,
--   nen chi muon muc cua QCVN lam moc, khong coi la nguong phap ly.
--
-- Bien (xu ly trong view cua schema):
--   KPI cang cao cang tot (cssr, user_throughput): '[)', min tinh vao: cssr 98 -> good, 95 -> medium.
--   KPI cang thap cang tot (service_drop_all): '(]', max tinh vao, khop QCVN "<= 2 %" va "<= 5 %":
--   good <= 2; medium > 2 den <= 5; poor > 5.

SET search_path = n46, public;

DELETE FROM kpi_thresholds t
USING kpis k
WHERE t.kpi_id = k.kpi_id
  AND t.threshold_type = 'team_proposed'
  AND k.kpi_code IN ('cssr', 'service_drop_all', 'user_throughput');

INSERT INTO kpi_thresholds
    (kpi_id, quality_level, min_value, max_value, threshold_type, threshold_basis,
     reference_name, reference_url, notes)
SELECT k.kpi_id, v.lv, v.lo, v.hi, 'team_proposed', v.basis, v.ref, v.url, v.note
FROM (VALUES
    -- cssr (%), cang cao cang tot
    ('cssr', 'good', 98::numeric, NULL::numeric,
     'Tuong ung ty le thiet lap khong thanh cong <= 2 % cua QCVN 36:2022/BTTTT.',
     'QCVN 36:2022/BTTTT (Thong tu 19/2022/TT-BTTTT), chi tieu ty le cuoc goi thiet lap khong thanh cong <= 2 %',
     'https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Thong-tu-19-2022-TT-BTTTT-Quy-chuan-chat-luong-dich-vu-dien-thoai-tren-mang-vien-thong-di-dong-542064.aspx',
     'QCVN do cuoc goi dau cuoi; CSSR du an la E-RAB theo cell/gio.'),
    ('cssr', 'medium', 95, 98,
     'Duoi muc QCVN 36:2022 nhung con trong muc truy nhap khong thanh cong <= 5 % cua QCVN 81:2019/BTTTT.',
     'QCVN 81:2019/BTTTT, chi tieu ty le truy nhap khong thanh cong dich vu <= 5 %',
     'https://tqc.gov.vn/ket-qua-do-kiem-cac-chi-tieu-chat-luong-ky-thuat-theo-quy-chuan-ky-thuat-quoc-gia-qcvn-812019-btttt-doi-voi-dich-vu-truy-nhap-internet-tren-mang-vien-thong-di-dong-mat-dat-su-dung-cong-nghe-lte-lte/',
     NULL),
    ('cssr', 'poor', NULL, 95,
     'Thap hon ca hai muc QCVN 36:2022 va QCVN 81:2019.',
     'QCVN 81:2019/BTTTT, chi tieu ty le truy nhap khong thanh cong dich vu <= 5 %',
     NULL, NULL),

    -- service_drop_all (%), cang thap cang tot
    ('service_drop_all', 'good', NULL, 2,
     'Tuong ung ty le cuoc goi bi roi <= 2 % cua QCVN 36:2022/BTTTT.',
     'QCVN 36:2022/BTTTT (Thong tu 19/2022/TT-BTTTT), chi tieu ty le cuoc goi bi roi <= 2 %',
     'https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Thong-tu-19-2022-TT-BTTTT-Quy-chuan-chat-luong-dich-vu-dien-thoai-tren-mang-vien-thong-di-dong-542064.aspx',
     'Service Drop All la cong thuc de xuat theo thuc tien van hanh, khong phai cong thuc 3GPP; dang cho Mentor VNPT xac nhan.'),
    ('service_drop_all', 'medium', 2, 5,
     'Vuot muc QCVN 36:2022 nhung con trong muc truyen tai du lieu bi roi <= 5 % cua QCVN 81:2019/BTTTT.',
     'QCVN 81:2019/BTTTT, chi tieu ty le truyen tai du lieu bi roi <= 5 %',
     'https://tqc.gov.vn/ket-qua-do-kiem-cac-chi-tieu-chat-luong-ky-thuat-theo-quy-chuan-ky-thuat-quoc-gia-qcvn-812019-btttt-doi-voi-dich-vu-truy-nhap-internet-tren-mang-vien-thong-di-dong-mat-dat-su-dung-cong-nghe-lte-lte/',
     NULL),
    ('service_drop_all', 'poor', 5, NULL,
     'Vuot ca hai muc QCVN 36:2022 va QCVN 81:2019.',
     'QCVN 81:2019/BTTTT, chi tieu ty le truyen tai du lieu bi roi <= 5 %',
     NULL, NULL),

    -- user_throughput (Mbps), cang cao cang tot
    ('user_throughput', 'good', 16, NULL,
     'Dat toc do tai xuong trung binh Vd = 16 Mbit/s ma VNPT cong bo theo QCVN 81:2019/BTTTT (do kiem Binh Dinh, 10-11/2024).',
     'QCVN 81:2019/BTTTT, chi tieu toc do tai xuong trung binh >= Vd; VNPT cong bo Vd = 16 Mbit/s',
     'https://tqc.gov.vn/ket-qua-do-kiem-cac-chi-tieu-chat-luong-ky-thuat-theo-quy-chuan-ky-thuat-quoc-gia-qcvn-812019-btttt-doi-voi-dich-vu-truy-nhap-internet-tren-mang-vien-thong-di-dong-mat-dat-su-dung-cong-nghe-lte-lte/',
     'QCVN khong dat so co dinh; Vd do doanh nghiep tu cong bo va co the doi theo dot.'),
    ('user_throughput', 'medium', 5, 16,
     'Duoi Vd nhung dat Vdmin = 5 Mbit/s ma VNPT cong bo theo QCVN 81:2019/BTTTT.',
     'QCVN 81:2019/BTTTT, chi tieu ty le mau co toc do tai xuong >= Vdmin; VNPT cong bo Vdmin = 5 Mbit/s',
     'https://tqc.gov.vn/ket-qua-do-kiem-cac-chi-tieu-chat-luong-ky-thuat-theo-quy-chuan-ky-thuat-quoc-gia-qcvn-812019-btttt-doi-voi-dich-vu-truy-nhap-internet-tren-mang-vien-thong-di-dong-mat-dat-su-dung-cong-nghe-lte-lte/',
     NULL),
    ('user_throughput', 'poor', NULL, 5,
     'Duoi Vdmin = 5 Mbit/s.',
     'QCVN 81:2019/BTTTT, chi tieu ty le mau co toc do tai xuong >= Vdmin; VNPT cong bo Vdmin = 5 Mbit/s',
     NULL, NULL)
) AS v(kpi_code, lv, lo, hi, basis, ref, url, note)
JOIN kpis k ON k.kpi_code = v.kpi_code;

-- Kiem tra: ca 3 KPI phai ra 'ok'.
SELECT kpi_code, levels, check_result FROM v_kpi_threshold_check ORDER BY kpi_code;
