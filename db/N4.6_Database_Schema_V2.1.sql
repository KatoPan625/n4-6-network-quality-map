-- =====================================================================
-- N4.6 - Ban do so hien thi chat luong mang theo khu vuc
-- Database Schema V2.1 - Mang co dinh | Grid 1 km | Theo tuan | Mo phong
-- Dich: PostgreSQL 17 + PostGIS 3.5.2 (da chay thu tren PG 16 + PostGIS 3.4.2)
-- Ban sua tu V2 cua Dat; xem tai lieu .md di kem, muc "Thay doi so voi V2".
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;   -- can cho rang buoc EXCLUDE cua kpi_thresholds

-- ---------------------------------------------------------------------
-- 1. study_areas - Pham vi nghien cuu (khung de sinh luoi)
-- ---------------------------------------------------------------------
CREATE TABLE study_areas (
    area_id      BIGSERIAL PRIMARY KEY,
    area_code    TEXT         NOT NULL UNIQUE,
    area_name    VARCHAR(255) NOT NULL,
    description  TEXT         NOT NULL,
    geom         geometry(MultiPolygon, 4326) NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT study_areas_geom_valid_chk CHECK (ST_IsValid(geom))
);

-- ---------------------------------------------------------------------
-- 2. regions - O luoi (va cap phuong/xa du phong)
-- ---------------------------------------------------------------------
CREATE TABLE regions (
    region_id         BIGSERIAL PRIMARY KEY,
    region_code       TEXT         NOT NULL UNIQUE,      -- G1K-<i>-<j>; ma trao doi voi API/Frontend
    region_name       VARCHAR(255) NOT NULL,
    region_level      VARCHAR(20)  NOT NULL DEFAULT 'grid_1km',
    parent_region_id  BIGINT       REFERENCES regions(region_id),
    area_id           BIGINT       REFERENCES study_areas(area_id),
    grid_col          INTEGER,                           -- i cua ST_SquareGrid trong EPSG:32648
    grid_row          INTEGER,                           -- j cua ST_SquareGrid trong EPSG:32648
    grid_size_m       SMALLINT,
    geom              geometry(MultiPolygon, 4326) NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT regions_level_chk CHECK (region_level IN ('grid_1km', 'grid_500m', 'ward')),
    CONSTRAINT regions_grid_fields_chk CHECK (
           (region_level = 'grid_1km'  AND grid_size_m = 1000 AND grid_col IS NOT NULL AND grid_row IS NOT NULL)
        OR (region_level = 'grid_500m' AND grid_size_m = 500  AND grid_col IS NOT NULL AND grid_row IS NOT NULL)
        OR (region_level = 'ward'      AND grid_size_m IS NULL AND grid_col IS NULL     AND grid_row IS NULL)
    ),
    CONSTRAINT regions_grid_cell_uq UNIQUE (region_level, grid_col, grid_row),
    CONSTRAINT regions_geom_valid_chk CHECK (ST_IsValid(geom))
);
CREATE INDEX regions_geom_gix   ON regions USING GIST (geom);
CREATE INDEX regions_parent_idx ON regions (parent_region_id);

-- ---------------------------------------------------------------------
-- 3. kpis - Danh muc KPI
-- ---------------------------------------------------------------------
CREATE TABLE kpis (
    kpi_id              BIGSERIAL PRIMARY KEY,
    kpi_code            TEXT          NOT NULL UNIQUE,
    kpi_name            VARCHAR(180)  NOT NULL,
    kpi_group           VARCHAR(50)   NOT NULL,
    unit                VARCHAR(30)   NOT NULL,
    higher_is_better    BOOLEAN       NOT NULL,
    is_ratio            BOOLEAN       NOT NULL,          -- TRUE: value = numerator / denominator x 100
    valid_min           NUMERIC(18,6) NOT NULL DEFAULT 0,
    valid_max           NUMERIC(18,6),                   -- NULL = khong co can tren
    description         TEXT          NOT NULL,
    calculation_method  TEXT          NOT NULL,
    aggregation_method  TEXT          NOT NULL,
    reference_name      TEXT,                            -- tai lieu dinh nghia KPI
    display_order       SMALLINT      NOT NULL,
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT kpis_group_chk CHECK (kpi_group IN (
        'internet_performance', 'internet_stability', 'availability',
        'service_access', 'session_continuity')),
    CONSTRAINT kpis_unit_chk  CHECK (unit IN ('Mbps', 'ms', '%')),
    CONSTRAINT kpis_ratio_unit_chk CHECK (is_ratio = (unit = '%')),
    CONSTRAINT kpis_range_chk CHECK (valid_max IS NULL OR valid_min < valid_max)
);

-- ---------------------------------------------------------------------
-- 4. kpi_thresholds - Nguong tot / trung binh / kem
--    Quy uoc khoang nua mo [min_value, max_value); NULL = khong gioi han.
-- ---------------------------------------------------------------------
CREATE TABLE kpi_thresholds (
    threshold_id     BIGSERIAL PRIMARY KEY,
    kpi_id           BIGINT        NOT NULL REFERENCES kpis(kpi_id) ON DELETE CASCADE,
    quality_level    VARCHAR(10)   NOT NULL,
    min_value        NUMERIC(18,6),
    max_value        NUMERIC(18,6),
    threshold_type   VARCHAR(20)   NOT NULL,
    threshold_basis  TEXT          NOT NULL,
    reference_name   TEXT,
    reference_url    TEXT,
    notes            TEXT,
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT kpi_thresholds_level_chk CHECK (quality_level IN ('good', 'medium', 'poor')),
    CONSTRAINT kpi_thresholds_type_chk  CHECK (threshold_type IN ('standard', 'team_proposed')),
    CONSTRAINT kpi_thresholds_bound_chk CHECK (min_value IS NOT NULL OR max_value IS NOT NULL),
    CONSTRAINT kpi_thresholds_order_chk CHECK (min_value IS NULL OR max_value IS NULL OR min_value < max_value),
    CONSTRAINT kpi_thresholds_ref_chk   CHECK (threshold_type = 'team_proposed' OR reference_name IS NOT NULL),
    CONSTRAINT kpi_thresholds_level_uq  UNIQUE (kpi_id, quality_level),
    CONSTRAINT kpi_thresholds_no_overlap EXCLUDE USING GIST (
        kpi_id WITH =,
        numrange(min_value, max_value, '[)') WITH &&)
);

-- ---------------------------------------------------------------------
-- 5. data_sources - Nguon du lieu
-- ---------------------------------------------------------------------
CREATE TABLE data_sources (
    source_id          BIGSERIAL PRIMARY KEY,
    source_code        TEXT          NOT NULL UNIQUE,
    source_name        VARCHAR(255)  NOT NULL,
    source_type        VARCHAR(40)   NOT NULL,
    data_nature        VARCHAR(20)   NOT NULL,
    description        TEXT          NOT NULL,
    spatial_scope      TEXT          NOT NULL,
    period_from        DATE          NOT NULL,           -- thu Hai tuan dau
    period_to          DATE          NOT NULL,           -- Chu nhat tuan cuoi
    collection_method  TEXT          NOT NULL,
    method_version     TEXT,                             -- phien ban script sinh/nap du lieu
    random_seed        BIGINT,                           -- de tai tao du lieu mo phong
    assumptions        TEXT          NOT NULL,
    limitations        TEXT          NOT NULL,
    source_url         TEXT,
    is_default         BOOLEAN       NOT NULL DEFAULT FALSE,  -- nguon API dung khi khong chi dinh
    created_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT data_sources_type_chk   CHECK (source_type IN (
        'simulation', 'public_dataset', 'field_measurement', 'company_data', 'other')),
    CONSTRAINT data_sources_nature_chk CHECK (data_nature IN ('real', 'simulated')),
    CONSTRAINT data_sources_sim_chk    CHECK (source_type <> 'simulation' OR data_nature = 'simulated'),
    CONSTRAINT data_sources_period_chk CHECK (
        period_from <= period_to
        AND EXTRACT(ISODOW FROM period_from) = 1
        AND EXTRACT(ISODOW FROM period_to)   = 7)
);
CREATE UNIQUE INDEX data_sources_one_default_uq ON data_sources (is_default) WHERE is_default;

-- ---------------------------------------------------------------------
-- 6. kpi_values - Gia tri KPI tong hop theo o luoi x tuan x nguon
-- ---------------------------------------------------------------------
CREATE TABLE kpi_values (
    kpi_value_id       BIGSERIAL PRIMARY KEY,
    source_id          BIGINT        NOT NULL REFERENCES data_sources(source_id),
    region_id          BIGINT        NOT NULL REFERENCES regions(region_id),
    kpi_id             BIGINT        NOT NULL REFERENCES kpis(kpi_id),
    period_type        VARCHAR(10)   NOT NULL DEFAULT 'week',
    period_start       DATE          NOT NULL,
    value              NUMERIC(18,6),
    status             VARCHAR(10)   NOT NULL DEFAULT 'ok',
    sample_count       INTEGER       NOT NULL DEFAULT 0,
    numerator_value    NUMERIC(20,6),
    denominator_value  NUMERIC(20,6),
    quality_note       TEXT,
    updated_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT kpi_values_period_type_chk CHECK (period_type = 'week'),
    CONSTRAINT kpi_values_monday_chk      CHECK (EXTRACT(ISODOW FROM period_start) = 1),
    CONSTRAINT kpi_values_status_chk      CHECK (status IN ('ok', 'missing', 'invalid')),
    CONSTRAINT kpi_values_status_value_chk CHECK (
           (status = 'ok' AND value IS NOT NULL AND sample_count > 0)
        OR (status IN ('missing', 'invalid') AND value IS NULL)),
    CONSTRAINT kpi_values_invalid_note_chk CHECK (status <> 'invalid' OR quality_note IS NOT NULL),
    CONSTRAINT kpi_values_sample_chk      CHECK (sample_count >= 0),
    CONSTRAINT kpi_values_ratio_pair_chk  CHECK ((numerator_value IS NULL) = (denominator_value IS NULL)),
    CONSTRAINT kpi_values_ratio_range_chk CHECK (
        denominator_value IS NULL
        OR (denominator_value > 0 AND numerator_value >= 0 AND numerator_value <= denominator_value)),
    CONSTRAINT kpi_values_uq UNIQUE (source_id, kpi_id, period_start, region_id)
);
-- kpi_values_uq phuc vu truy van ban do (1 nguon, 1 KPI, 1 tuan, moi o).
CREATE INDEX kpi_values_region_history_idx ON kpi_values (source_id, region_id, kpi_id, period_start);

-- Kiem tra phu thuoc bang kpis: mien gia tri, va value = tu/mau x 100 voi KPI ti le.
CREATE FUNCTION kpi_values_validate() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    k kpis%ROWTYPE;
    p_from DATE; p_to DATE;
BEGIN
    SELECT * INTO k FROM kpis WHERE kpi_id = NEW.kpi_id;
    SELECT period_from, period_to INTO p_from, p_to FROM data_sources WHERE source_id = NEW.source_id;

    IF NEW.period_start < p_from OR NEW.period_start + 6 > p_to THEN
        RAISE EXCEPTION 'period_start % nam ngoai khoang cua nguon du lieu (% - %)',
            NEW.period_start, p_from, p_to;
    END IF;

    IF NEW.status = 'ok' THEN
        IF NEW.value < k.valid_min OR (k.valid_max IS NOT NULL AND NEW.value > k.valid_max) THEN
            RAISE EXCEPTION 'KPI %: value % ngoai mien [%, %]',
                k.kpi_code, NEW.value, k.valid_min, COALESCE(k.valid_max::text, 'khong gioi han');
        END IF;
        IF k.is_ratio THEN
            IF NEW.numerator_value IS NULL THEN
                RAISE EXCEPTION 'KPI % la ti le: can numerator_value va denominator_value', k.kpi_code;
            END IF;
            IF abs(NEW.value - NEW.numerator_value / NEW.denominator_value * 100) > 0.0001 THEN
                RAISE EXCEPTION 'KPI %: value % khong khop tu/mau so (%)', k.kpi_code, NEW.value,
                    round(NEW.numerator_value / NEW.denominator_value * 100, 6);
            END IF;
        ELSIF NEW.numerator_value IS NOT NULL THEN
            RAISE EXCEPTION 'KPI % khong phai ti le: bo trong numerator/denominator', k.kpi_code;
        END IF;
    END IF;

    NEW.updated_at := NOW();
    RETURN NEW;
END $$;

CREATE TRIGGER kpi_values_validate_trg
    BEFORE INSERT OR UPDATE ON kpi_values
    FOR EACH ROW EXECUTE FUNCTION kpi_values_validate();

-- ---------------------------------------------------------------------
-- 7. View cho API: gia tri kem muc chat luong va nhan nguon
-- ---------------------------------------------------------------------
CREATE VIEW v_kpi_values_classified AS
SELECT
    v.kpi_value_id,
    r.region_code,
    k.kpi_code,
    k.unit,
    k.higher_is_better,
    v.period_type,
    v.period_start,
    v.value,
    v.status,
    v.sample_count,
    t.quality_level,                     -- NULL khi chua co nguong hoac status <> 'ok'
    t.threshold_type,
    s.source_code,
    s.data_nature,                       -- 'simulated' -> Frontend hien nhan "Du lieu mo phong"
    v.quality_note
FROM kpi_values v
JOIN regions      r ON r.region_id = v.region_id
JOIN kpis         k ON k.kpi_id    = v.kpi_id
JOIN data_sources s ON s.source_id = v.source_id
LEFT JOIN kpi_thresholds t
       ON t.kpi_id = v.kpi_id
      AND v.status = 'ok'
      AND v.value::numeric <@ numrange(t.min_value, t.max_value, '[)');

-- Kiem tra nguong: moi KPI du 3 muc, khong ho, dung chieu tot/kem.
-- Chieu cao tot:  poor [NULL, a) - medium [a, b) - good [b, NULL)
-- Chieu thap tot: good [NULL, a) - medium [a, b) - poor [b, NULL)
CREATE VIEW v_kpi_threshold_check AS
WITH p AS (
    SELECT k.kpi_code, k.higher_is_better,
           max(t.min_value) FILTER (WHERE t.quality_level = 'good')   AS good_min,
           max(t.max_value) FILTER (WHERE t.quality_level = 'good')   AS good_max,
           max(t.min_value) FILTER (WHERE t.quality_level = 'medium') AS med_min,
           max(t.max_value) FILTER (WHERE t.quality_level = 'medium') AS med_max,
           max(t.min_value) FILTER (WHERE t.quality_level = 'poor')   AS poor_min,
           max(t.max_value) FILTER (WHERE t.quality_level = 'poor')   AS poor_max,
           count(t.threshold_id) AS levels
    FROM kpis k LEFT JOIN kpi_thresholds t ON t.kpi_id = k.kpi_id
    WHERE k.is_active
    GROUP BY k.kpi_code, k.higher_is_better
)
SELECT kpi_code, levels,
       CASE
         WHEN levels < 3 THEN 'thieu muc'
         WHEN higher_is_better AND poor_min IS NULL AND poor_max = med_min
              AND med_max = good_min AND good_max IS NULL THEN 'ok'
         WHEN NOT higher_is_better AND good_min IS NULL AND good_max = med_min
              AND med_max = poor_min AND poor_max IS NULL THEN 'ok'
         ELSE 'ho hoac sai chieu'
       END AS check_result
FROM p;

-- =====================================================================
-- DU LIEU KHOI TAO
-- =====================================================================

-- 8 KPI mang co dinh
INSERT INTO kpis (kpi_code, kpi_name, kpi_group, unit, higher_is_better, is_ratio, valid_min, valid_max,
                  description, calculation_method, aggregation_method, reference_name, display_order) VALUES
('download_throughput', 'Download Throughput', 'internet_performance', 'Mbps', TRUE, FALSE, 0, NULL,
 'Toc do tai xuong do duoc.', 'Du lieu tai xuong / thoi gian truyen (Mbps).',
 'Trung vi cac phep do hop le trong tuan.', 'ITU-T Y.1540; QCVN 34:2022/BTTTT', 1),
('upload_throughput', 'Upload Throughput', 'internet_performance', 'Mbps', TRUE, FALSE, 0, NULL,
 'Toc do tai len do duoc.', 'Du lieu tai len / thoi gian truyen (Mbps).',
 'Trung vi cac phep do hop le trong tuan.', 'ITU-T Y.1540; QCVN 34:2022/BTTTT', 2),
('latency', 'Latency (RTT)', 'internet_performance', 'ms', FALSE, FALSE, 0, NULL,
 'Thoi gian khu hoi cua goi tin.', 'Thoi diem nhan phan hoi - thoi diem gui (ms).',
 'Trung vi cac phep do hop le trong tuan.', 'ITU-T Y.1540 (IPTD)', 3),
('jitter', 'Jitter', 'internet_stability', 'ms', FALSE, FALSE, 0, NULL,
 'Do bien thien do tre.', 'Bien thien do tre giua cac goi lien tiep (ms).',
 'Trung vi cac phep do hop le trong tuan.', 'ITU-T Y.1540 (IPDV)', 4),
('packet_loss_rate', 'Packet Loss Rate', 'internet_stability', '%', FALSE, TRUE, 0, 100,
 'Ti le goi tin bi mat.', 'Goi mat / goi gui x 100.',
 'Tong goi mat trong tuan / tong goi gui trong tuan x 100.', 'ITU-T Y.1540 (IPLR)', 5),
('network_availability', 'Network Availability', 'availability', '%', TRUE, TRUE, 0, 100,
 'Ti le thoi gian ket noi san sang.', 'Thoi gian san sang / tong thoi gian giam sat x 100.',
 'Tong thoi gian san sang trong tuan / tong thoi gian giam sat x 100.', 'ITU-T Y.1540 (availability)', 6),
('http_ip_access_failure_ratio', 'HTTP IP-Service Access Failure Ratio', 'service_access', '%', FALSE, TRUE, 0, 100,
 'Ti le lan thu khong thiet lap duoc ket noi TCP/IP toi may chu HTTP.',
 'Lan thiet lap that bai / tong lan thu x 100.',
 'Tong lan that bai trong tuan / tong lan thu trong tuan x 100.', 'ETSI TS 103 222-2 V1.3.1', 7),
('http_dropped_sessions_ratio', 'HTTP Dropped Sessions Ratio', 'session_continuity', '%', FALSE, TRUE, 0, 100,
 'Ti le phien HTTP bi ngat ngoai y muon.', 'Phien bi ngat / tong phien da bat dau x 100.',
 'Tong phien bi ngat trong tuan / tong phien trong tuan x 100.', 'ETSI TS 103 222-2 V1.3.1', 8);

-- Khung nghien cuu mac dinh: 15 km x 11 km, tu khu Ben Thanh mo rong ve phia Thu Duc cu.
-- Toa do canh theo boi so 1000 m trong EPSG:32648 de moi o la o 1 km tron ven.
-- Doi khung: chi sua 4 so trong ST_MakeEnvelope roi chay lai buoc sinh luoi.
INSERT INTO study_areas (area_code, area_name, description, geom)
SELECT 'HCM-CENTER-NE',
       'Khung trung tam - Thu Duc cu',
       'Hinh chu nhat 15 km (Dong-Tay) x 11 km (Bac-Nam) trong EPSG:32648, '
       || 'X 683000-698000, Y 1190000-1201000; gom khu Ben Thanh, Thu Thiem, Thao Dien, An Phu, mot phan Thu Duc cu.',
       ST_Multi(ST_Transform(ST_MakeEnvelope(683000, 1190000, 698000, 1201000, 32648), 4326));

-- Sinh luoi 1 km. i, j lay tu ST_SquareGrid voi goc mac dinh (0,0) cua EPSG:32648,
-- nen ma o khong doi khi mo rong khung. Khong doi CRS, kich thuoc hay goc.
-- ST_SnapToGrid loai sai so lam tron khi doi 4326 -> 32648; dieu kien NOT ST_Touches
-- bo cac o chi cham canh khung.
INSERT INTO regions (region_code, region_name, region_level, area_id, grid_col, grid_row, grid_size_m, geom)
SELECT format('G1K-%s-%s', g.i, g.j),
       format('O %s-%s', g.i, g.j),
       'grid_1km', a.area_id, g.i, g.j, 1000,
       ST_Multi(ST_Transform(g.geom, 4326))
FROM study_areas a
CROSS JOIN LATERAL ST_SquareGrid(1000, ST_SnapToGrid(ST_Transform(a.geom, 32648), 1)) AS g
WHERE a.area_code = 'HCM-CENTER-NE'
  AND ST_Intersects(g.geom, ST_SnapToGrid(ST_Transform(a.geom, 32648), 1))
  AND NOT ST_Touches(g.geom, ST_SnapToGrid(ST_Transform(a.geom, 32648), 1))
ON CONFLICT (region_code) DO NOTHING;

-- Nguon du lieu mo phong mac dinh: 26 tuan, 04/05/2026 - 01/11/2026.
INSERT INTO data_sources (source_code, source_name, source_type, data_nature, description, spatial_scope,
                          period_from, period_to, collection_method, method_version, random_seed,
                          assumptions, limitations, is_default)
VALUES ('SIM-V1', 'Bo du lieu mo phong N4.6 v1', 'simulation', 'simulated',
        '8 KPI mang co dinh, tong hop theo o luoi 1 km va theo tuan.',
        'Khung HCM-CENTER-NE (bang study_areas), luoi 1 km.',
        DATE '2026-05-04', DATE '2026-11-01',
        'Vu dien: thuat toan sinh, bo tham so, cach tong hop.', 'v1', 20261118,
        'Vu dien: chi cac gia dinh thuc su ap dung.',
        'Khong phai so lieu do thuc te cua VNPT; khong dung de ket luan chat luong mang thuc te.',
        TRUE);

-- Mau them nguong (KHONG chay khi chua co can cu):
-- INSERT INTO kpi_thresholds (kpi_id, quality_level, min_value, max_value, threshold_type,
--                             threshold_basis, reference_name, reference_url, notes)
-- SELECT kpi_id, 'good', <min>, NULL, 'standard', '<trich dan dieu, muc>', 'QCVN 34:2022/BTTTT', '<url>', NULL
-- FROM kpis WHERE kpi_code = 'download_throughput';
