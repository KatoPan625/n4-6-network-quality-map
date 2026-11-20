-- ============================================================================
-- N4.6 - BAN DO SO HIEN THI CHAT LUONG MANG THEO KHU VUC
-- DATABASE SCHEMA - MANG DI DONG 4G | CELL / GIO | 30 NGAY
-- PostgreSQL + PostGIS
-- Namespace co dinh: n46 (khong gan so phien ban vao ten schema).
-- Thiet ke chi tiet: docs/SCHEMA.md.
-- Luu y: SQL tao cau truc + danh muc 4 KPI + nguon mo phong mau; khong tao cell/value gia.
--       Can nap GeoJSON (34 tinh + 168 phuong/xa TP.HCM) va danh sach cell.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS n46;

BEGIN;
SET LOCAL search_path TO n46, public;

-- Remove the two superseded classified views; classification is now included
-- directly in the two aggregation views.
DROP VIEW IF EXISTS v_region_kpi_classified;
DROP VIEW IF EXISTS v_region_kpi_daily_classified;

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;

-- ---------------------------------------------------------------------------
-- 1. regions: don vi hanh chinh. Chi nap 34 tinh va 168 phuong/xa TP.HCM.
--    region_code dung ma hanh chinh chinh thuc, khong dung ten de lien ket.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regions (
    region_id         BIGSERIAL PRIMARY KEY,
    region_code       TEXT NOT NULL UNIQUE,
    region_name       VARCHAR(255) NOT NULL,
    region_level      VARCHAR(20) NOT NULL,
    parent_region_id  BIGINT REFERENCES regions(region_id),
    geom              geometry(MultiPolygon, 4326) NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT regions_level_chk CHECK (region_level IN ('province', 'ward')),
    CONSTRAINT regions_parent_shape_chk CHECK (
        (region_level = 'province' AND parent_region_id IS NULL)
        OR (region_level = 'ward' AND parent_region_id IS NOT NULL)
    ),
    CONSTRAINT regions_geom_valid_chk CHECK (ST_IsValid(geom) AND NOT ST_IsEmpty(geom))
);
CREATE INDEX IF NOT EXISTS regions_geom_gix ON regions USING GIST (geom);
CREATE INDEX IF NOT EXISTS regions_parent_idx ON regions (parent_region_id);
CREATE INDEX IF NOT EXISTS regions_level_idx ON regions (region_level);

CREATE OR REPLACE FUNCTION validate_region_hierarchy()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE parent_level TEXT;
BEGIN
    IF NEW.region_level = 'province' THEN
        IF NEW.parent_region_id IS NOT NULL THEN
            RAISE EXCEPTION 'Province region must not have parent_region_id';
        END IF;
    ELSE
        SELECT region_level INTO parent_level
        FROM regions WHERE region_id = NEW.parent_region_id;
        IF parent_level IS DISTINCT FROM 'province' THEN
            RAISE EXCEPTION 'Ward region must reference a province region';
        END IF;
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS regions_hierarchy_trg ON regions;
CREATE TRIGGER regions_hierarchy_trg
BEFORE INSERT OR UPDATE ON regions
FOR EACH ROW EXECUTE FUNCTION validate_region_hierarchy();

-- ---------------------------------------------------------------------------
-- 2. cells: cell logic, khong luu toa do tram/cell.
--    province_id bat buoc de tong hop 34 tinh; ward_id NULL neu chi co du lieu tinh.
--    Neu mot tinh da co ban ghi ward thi moi cell cua tinh do bat buoc gan ward_id.
--    Neu ward_id duoc gan thi ward phai thuoc dung province_id; tinh chua nap ward duoc phep ward_id=NULL.
--    Giai doan demo: danh sach cell co dinh trong ca khoang 30 ngay; is_active ap dung cho toan bo ky.
--    Khong luu active_from/active_to trong pham vi demo; day la gia dinh/han che duoc ghi o data_sources.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cells (
    cell_id       BIGSERIAL PRIMARY KEY,
    cell_code     TEXT NOT NULL UNIQUE,
    province_id   BIGINT NOT NULL REFERENCES regions(region_id),
    ward_id       BIGINT REFERENCES regions(region_id),
    rat           VARCHAR(8) NOT NULL DEFAULT '4G',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT cells_rat_chk CHECK (rat IN ('4G', '5G'))
);
-- Idempotent adjustment when an earlier n46 draft had a 4G-only RAT check.
ALTER TABLE cells DROP CONSTRAINT IF EXISTS cells_rat_phase1_chk;
ALTER TABLE cells DROP CONSTRAINT IF EXISTS cells_rat_chk;
ALTER TABLE cells ADD CONSTRAINT cells_rat_chk CHECK (rat IN ('4G', '5G'));
CREATE INDEX IF NOT EXISTS cells_province_idx ON cells (province_id);
CREATE INDEX IF NOT EXISTS cells_ward_idx ON cells (ward_id) WHERE ward_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS cells_active_idx ON cells (is_active);

CREATE OR REPLACE FUNCTION validate_cell_region_links()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE province_level TEXT;
DECLARE ward_level TEXT;
DECLARE ward_parent BIGINT;
DECLARE province_has_wards BOOLEAN;
BEGIN
    SELECT region_level INTO province_level
    FROM regions WHERE region_id = NEW.province_id;
    IF province_level IS DISTINCT FROM 'province' THEN
        RAISE EXCEPTION 'cells.province_id must reference a province region';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM regions wr
        WHERE wr.region_level = 'ward'
          AND wr.parent_region_id = NEW.province_id
    ) INTO province_has_wards;

    IF province_has_wards AND NEW.ward_id IS NULL THEN
        RAISE EXCEPTION 'ward_id is required because province % has ward-level regions', NEW.province_id;
    END IF;

    IF NEW.ward_id IS NOT NULL THEN
        SELECT region_level, parent_region_id
          INTO ward_level, ward_parent
        FROM regions WHERE region_id = NEW.ward_id;
        IF ward_level IS DISTINCT FROM 'ward' OR ward_parent IS DISTINCT FROM NEW.province_id THEN
            RAISE EXCEPTION 'cells.ward_id must reference a ward belonging to cells.province_id';
        END IF;
    END IF;

    NEW.updated_at := NOW();
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS cells_region_links_trg ON cells;
CREATE TRIGGER cells_region_links_trg
BEFORE INSERT OR UPDATE ON cells
FOR EACH ROW EXECUTE FUNCTION validate_cell_region_links();


-- If ward boundaries are imported after cells, do not allow a province to gain
-- ward-level children while it still has cells with ward_id NULL. Import all
-- province/ward regions before importing cells.
CREATE OR REPLACE FUNCTION guard_region_ward_coverage()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.region_level = 'ward' THEN
        IF EXISTS (
            SELECT 1
            FROM cells c
            WHERE c.province_id = NEW.parent_region_id
              AND c.ward_id IS NULL
        ) THEN
            RAISE EXCEPTION 'Cannot add/reparent ward: province % has cells without ward_id', NEW.parent_region_id;
        END IF;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF OLD.region_level = 'ward'
           AND (NEW.region_level <> 'ward'
                OR NEW.parent_region_id IS DISTINCT FROM OLD.parent_region_id)
           AND EXISTS (SELECT 1 FROM cells c WHERE c.ward_id = OLD.region_id) THEN
            RAISE EXCEPTION 'Cannot change ward hierarchy while cells reference ward %', OLD.region_id;
        END IF;
    END IF;

    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS regions_ward_coverage_trg ON regions;
CREATE TRIGGER regions_ward_coverage_trg
BEFORE INSERT OR UPDATE ON regions
FOR EACH ROW EXECUTE FUNCTION guard_region_ward_coverage();

-- ---------------------------------------------------------------------------
-- 3. data_sources: nguon du lieu va thoi gian hieu luc.
--    period_to la moc KET THUC KHONG BAO GOM (exclusive).
--    Khoang mau 01-30/10/2026 = [01/10 00:00, 31/10 00:00) gio VN = 720 gio.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_sources (
    source_id          BIGSERIAL PRIMARY KEY,
    source_code        TEXT NOT NULL UNIQUE,
    source_name        VARCHAR(255) NOT NULL,
    source_type        VARCHAR(40) NOT NULL,
    data_nature        VARCHAR(20) NOT NULL,
    description        TEXT NOT NULL,
    spatial_scope      TEXT NOT NULL,
    period_from        TIMESTAMPTZ NOT NULL,
    period_to          TIMESTAMPTZ NOT NULL,
    timezone_name      TEXT NOT NULL DEFAULT 'Asia/Ho_Chi_Minh',
    collection_method  TEXT NOT NULL,
    method_version     TEXT,
    random_seed        BIGINT,
    assumptions        TEXT NOT NULL,
    limitations        TEXT NOT NULL,
    source_url         TEXT,
    is_default         BOOLEAN NOT NULL DEFAULT FALSE,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT data_sources_type_chk CHECK (source_type IN ('simulation', 'public_dataset', 'field_measurement', 'company_data', 'other')),
    CONSTRAINT data_sources_nature_chk CHECK (data_nature IN ('real', 'simulated')),
    CONSTRAINT data_sources_simulation_chk CHECK (source_type <> 'simulation' OR data_nature = 'simulated'),
    CONSTRAINT data_sources_period_chk CHECK (period_from < period_to),
    CONSTRAINT data_sources_timezone_chk CHECK (timezone_name = 'Asia/Ho_Chi_Minh'),
    CONSTRAINT data_sources_default_active_chk CHECK (NOT is_default OR is_active)
);
CREATE UNIQUE INDEX IF NOT EXISTS data_sources_one_default_uq
ON data_sources (is_default) WHERE is_default;

CREATE OR REPLACE FUNCTION validate_data_source_hours()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF date_trunc('hour', NEW.period_from AT TIME ZONE NEW.timezone_name)
       <> (NEW.period_from AT TIME ZONE NEW.timezone_name)
       OR date_trunc('hour', NEW.period_to AT TIME ZONE NEW.timezone_name)
       <> (NEW.period_to AT TIME ZONE NEW.timezone_name) THEN
        RAISE EXCEPTION 'period_from/period_to must align to a local hour in %', NEW.timezone_name;
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS data_sources_hours_trg ON data_sources;
CREATE TRIGGER data_sources_hours_trg
BEFORE INSERT OR UPDATE ON data_sources
FOR EACH ROW EXECUTE FUNCTION validate_data_source_hours();

-- ---------------------------------------------------------------------------
-- 4. kpis: danh muc KPI. Them KPI moi bang INSERT, khong doi cau truc bang value.
--    KPI chat luong phai traffic_weighted; traffic la KPI tong luong, dung SUM.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kpis (
    kpi_id              BIGSERIAL PRIMARY KEY,
    kpi_code            TEXT NOT NULL UNIQUE,
    kpi_name            VARCHAR(180) NOT NULL,
    kpi_group           VARCHAR(50) NOT NULL,
    unit                VARCHAR(20) NOT NULL,
    higher_is_better    BOOLEAN,
    is_quality_kpi      BOOLEAN NOT NULL DEFAULT TRUE,
    is_ratio            BOOLEAN NOT NULL DEFAULT FALSE,
    aggregation_rule    VARCHAR(30) NOT NULL,
    valid_min           NUMERIC(20,6) NOT NULL DEFAULT 0,
    valid_max           NUMERIC(20,6),
    description         TEXT NOT NULL,
    calculation_method  TEXT NOT NULL,
    reference_name      TEXT,
    display_order       SMALLINT NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT kpis_aggregation_chk CHECK (aggregation_rule IN ('sum', 'traffic_weighted')),
    CONSTRAINT kpis_quality_aggregation_chk CHECK (
        (is_quality_kpi = TRUE AND aggregation_rule = 'traffic_weighted')
        OR (is_quality_kpi = FALSE AND aggregation_rule = 'sum')
    ),
    CONSTRAINT kpis_ratio_unit_chk CHECK (is_ratio = (unit = '%')),
    CONSTRAINT kpis_quality_direction_chk CHECK (
        (is_quality_kpi = TRUE AND higher_is_better IS NOT NULL)
        OR (is_quality_kpi = FALSE AND higher_is_better IS NULL)
    ),
    CONSTRAINT kpis_range_chk CHECK (
        (valid_max IS NULL OR valid_min < valid_max)
        AND valid_min NOT IN ('NaN'::NUMERIC, 'Infinity'::NUMERIC, '-Infinity'::NUMERIC)
        AND (valid_max IS NULL OR valid_max NOT IN ('NaN'::NUMERIC, 'Infinity'::NUMERIC, '-Infinity'::NUMERIC))
    )
);

CREATE OR REPLACE FUNCTION touch_kpis_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS kpis_updated_at_trg ON kpis;
CREATE TRIGGER kpis_updated_at_trg
BEFORE UPDATE ON kpis
FOR EACH ROW EXECUTE FUNCTION touch_kpis_updated_at();

-- ---------------------------------------------------------------------------
-- 5. kpi_thresholds: nguong tot / trung binh / kem.
--    Khong seed nguong so khi chua co can cu duoc nhom xac nhan.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kpi_thresholds (
    threshold_id     BIGSERIAL PRIMARY KEY,
    kpi_id           BIGINT NOT NULL REFERENCES kpis(kpi_id) ON DELETE CASCADE,
    quality_level    VARCHAR(10) NOT NULL,
    min_value        NUMERIC(20,6),
    max_value        NUMERIC(20,6),
    threshold_type   VARCHAR(20) NOT NULL,
    threshold_basis  TEXT NOT NULL,
    reference_name   TEXT,
    reference_url    TEXT,
    notes            TEXT,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT kpi_thresholds_level_chk CHECK (quality_level IN ('good', 'medium', 'poor')),
    CONSTRAINT kpi_thresholds_type_chk CHECK (threshold_type IN ('standard', 'team_proposed')),
    CONSTRAINT kpi_thresholds_bound_chk CHECK (min_value IS NOT NULL OR max_value IS NOT NULL),
    CONSTRAINT kpi_thresholds_order_chk CHECK (
        (min_value IS NULL OR max_value IS NULL OR min_value < max_value)
        AND (min_value IS NULL OR min_value NOT IN ('NaN'::NUMERIC, 'Infinity'::NUMERIC, '-Infinity'::NUMERIC))
        AND (max_value IS NULL OR max_value NOT IN ('NaN'::NUMERIC, 'Infinity'::NUMERIC, '-Infinity'::NUMERIC))
    ),
    CONSTRAINT kpi_thresholds_ref_chk CHECK (threshold_type = 'team_proposed' OR reference_name IS NOT NULL),
    CONSTRAINT kpi_thresholds_level_uq UNIQUE (kpi_id, quality_level),
    CONSTRAINT kpi_thresholds_no_overlap EXCLUDE USING GIST (
        kpi_id WITH =,
        numrange(min_value, max_value, '[)') WITH &&
    )
);

CREATE OR REPLACE FUNCTION validate_threshold_kpi()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE k kpis%ROWTYPE;
BEGIN
    SELECT * INTO k FROM kpis WHERE kpi_id = NEW.kpi_id;
    IF k.kpi_id IS NULL OR k.is_quality_kpi IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'Thresholds can only be defined for an active quality KPI';
    END IF;
    IF NEW.min_value IS NOT NULL AND NEW.min_value < k.valid_min THEN
        RAISE EXCEPTION 'Threshold min_value is below KPI valid_min';
    END IF;
    IF NEW.max_value IS NOT NULL AND k.valid_max IS NOT NULL AND NEW.max_value > k.valid_max THEN
        RAISE EXCEPTION 'Threshold max_value is above KPI valid_max';
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS kpi_thresholds_quality_trg ON kpi_thresholds;
CREATE TRIGGER kpi_thresholds_quality_trg
BEFORE INSERT OR UPDATE ON kpi_thresholds
FOR EACH ROW EXECUTE FUNCTION validate_threshold_kpi();

-- ---------------------------------------------------------------------------
-- 6. cell_kpi_values: moi KPI mot dong / cell / gio / nguon.
--    Khong luu counter; luu truc tiep gia tri KPI da tinh.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cell_kpi_values (
    cell_kpi_value_id BIGSERIAL PRIMARY KEY,
    source_id         BIGINT NOT NULL REFERENCES data_sources(source_id),
    cell_id           BIGINT NOT NULL REFERENCES cells(cell_id),
    kpi_id            BIGINT NOT NULL REFERENCES kpis(kpi_id),
    period_start      TIMESTAMPTZ NOT NULL,
    value             NUMERIC(20,6),
    status            VARCHAR(10) NOT NULL DEFAULT 'ok',
    quality_note      TEXT,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT cell_kpi_values_status_chk CHECK (status IN ('ok', 'missing', 'invalid')),
    CONSTRAINT cell_kpi_values_value_status_chk CHECK (
        (status = 'ok' AND value IS NOT NULL)
        OR (status IN ('missing', 'invalid') AND value IS NULL)
    ),
    CONSTRAINT cell_kpi_values_invalid_note_chk CHECK (status <> 'invalid' OR quality_note IS NOT NULL),
    CONSTRAINT cell_kpi_values_finite_chk CHECK (value IS NULL OR value NOT IN ('NaN'::NUMERIC, 'Infinity'::NUMERIC, '-Infinity'::NUMERIC)),
    CONSTRAINT cell_kpi_values_unique UNIQUE (source_id, cell_id, kpi_id, period_start)
);
DROP INDEX IF EXISTS cell_kpi_values_kpi_hour_idx;
CREATE INDEX IF NOT EXISTS cell_kpi_values_source_kpi_hour_idx
ON cell_kpi_values (source_id, kpi_id, period_start);
CREATE INDEX IF NOT EXISTS cell_kpi_values_cell_history_idx
ON cell_kpi_values (cell_id, source_id, period_start, kpi_id);

CREATE OR REPLACE FUNCTION validate_cell_kpi_value()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    k kpis%ROWTYPE;
    s data_sources%ROWTYPE;
    local_hour TIMESTAMP;
BEGIN
    SELECT * INTO k FROM kpis WHERE kpi_id = NEW.kpi_id;
    SELECT * INTO s FROM data_sources WHERE source_id = NEW.source_id;
    IF k.kpi_id IS NULL OR s.source_id IS NULL THEN
        RAISE EXCEPTION 'Unknown KPI or data source';
    END IF;

    IF NEW.period_start < s.period_from OR NEW.period_start >= s.period_to THEN
        RAISE EXCEPTION 'period_start % is outside source period [% - %)', NEW.period_start, s.period_from, s.period_to;
    END IF;

    local_hour := NEW.period_start AT TIME ZONE s.timezone_name;
    IF date_trunc('hour', local_hour) <> local_hour THEN
        RAISE EXCEPTION 'period_start must be aligned to a local hour in %', s.timezone_name;
    END IF;

    IF NEW.status = 'ok' THEN
        IF NEW.value < k.valid_min OR (k.valid_max IS NOT NULL AND NEW.value > k.valid_max) THEN
            RAISE EXCEPTION 'KPI % value % outside valid range [%, %]', k.kpi_code, NEW.value, k.valid_min, k.valid_max;
        END IF;
    END IF;

    NEW.updated_at := NOW();
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS cell_kpi_values_validate_trg ON cell_kpi_values;
CREATE TRIGGER cell_kpi_values_validate_trg
BEFORE INSERT OR UPDATE ON cell_kpi_values
FOR EACH ROW EXECUTE FUNCTION validate_cell_kpi_value();

-- Co dinh search_path cho trigger functions trong dung schema.
ALTER FUNCTION n46.validate_region_hierarchy() SET search_path = pg_catalog, n46, public;
ALTER FUNCTION n46.validate_cell_region_links() SET search_path = pg_catalog, n46, public;
ALTER FUNCTION n46.guard_region_ward_coverage() SET search_path = pg_catalog, n46, public;
ALTER FUNCTION n46.validate_data_source_hours() SET search_path = pg_catalog, n46, public;
ALTER FUNCTION n46.validate_threshold_kpi() SET search_path = pg_catalog, n46, public;
ALTER FUNCTION n46.validate_cell_kpi_value() SET search_path = pg_catalog, n46, public;
ALTER FUNCTION n46.touch_kpis_updated_at() SET search_path = pg_catalog, n46, public;

-- ---------------------------------------------------------------------------
-- 7. VIEW v_region_kpi: tong hop THEO GIO cell -> ward / province.
--    Phan loai threshold khi value IS NOT NULL, ke ca status='partial'.
--    Bien: KPI cang cao cang tot dung '[)' (>= min); cang thap cang tot dung '(]' (<= max).
--    KPI quality: SUM(KPI_cell * traffic_cell) / SUM(traffic_cell)
--    cells_reported dem cell co KPI va Traffic hop le (Traffic co the = 0).
--    Mau so chi gom Traffic > 0 tren cung tap cell co KPI hop le; cell Traffic=0 khong dong gop trong so.
--    Traffic KPI: SUM traffic hop le cua tat ca cell trong region/hour.
--    traffic_total_gb va traffic_weight_gb duoc tach rieng de khong nham
--    tong traffic toan vung voi mau so thuc su dung lam trong so.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_region_kpi AS
WITH traffic_kpi AS (
    SELECT kpi_id FROM kpis WHERE kpi_code = 'traffic'
),
region_cells AS (
    SELECT r.region_id, c.cell_id
    FROM regions r
    JOIN cells c ON r.region_level = 'province' AND c.province_id = r.region_id AND c.is_active
    UNION ALL
    SELECT r.region_id, c.cell_id
    FROM regions r
    JOIN cells c ON r.region_level = 'ward' AND c.ward_id = r.region_id AND c.is_active
),
cell_counts AS (
    SELECT region_id, COUNT(*)::INTEGER AS cells_total
    FROM region_cells
    GROUP BY region_id
),
hours AS (
    SELECT s.source_id, s.source_code, s.data_nature, s.timezone_name, g.period_start
    FROM data_sources s
    CROSS JOIN LATERAL generate_series(
        s.period_from,
        s.period_to - INTERVAL '1 hour',
        INTERVAL '1 hour'
    ) AS g(period_start)
    WHERE s.is_active
),
region_scope AS (
    SELECT
        h.source_id, h.source_code, h.data_nature, h.timezone_name,
        r.region_id, r.region_code, r.region_name, r.region_level,
        k.kpi_id, k.kpi_code, k.kpi_name, k.unit, k.aggregation_rule,
        k.higher_is_better, k.is_quality_kpi,
        h.period_start,
        COALESCE(cc.cells_total, 0)::INTEGER AS cells_total
    FROM hours h
    CROSS JOIN regions r
    CROSS JOIN kpis k
    LEFT JOIN cell_counts cc ON cc.region_id = r.region_id
    WHERE k.is_active
),
traffic_rollup AS (
    SELECT
        rc.region_id,
        tv.source_id,
        tv.period_start,
        COUNT(DISTINCT rc.cell_id) FILTER (
            WHERE tv.status = 'ok' AND tv.value IS NOT NULL
        )::INTEGER AS traffic_cells_reported,
        SUM(tv.value) FILTER (
            WHERE tv.status = 'ok' AND tv.value IS NOT NULL
        ) AS traffic_total_gb,
        MAX(tv.updated_at) AS traffic_updated_at
    FROM region_cells rc
    JOIN cell_kpi_values tv ON tv.cell_id = rc.cell_id
    JOIN traffic_kpi tk ON tk.kpi_id = tv.kpi_id
    JOIN data_sources ds ON ds.source_id = tv.source_id AND ds.is_active
    GROUP BY rc.region_id, tv.source_id, tv.period_start
),
kpi_rollup AS (
    SELECT
        rc.region_id,
        v.source_id,
        v.kpi_id,
        v.period_start,
        COUNT(DISTINCT rc.cell_id) FILTER (
            WHERE v.status = 'ok' AND v.value IS NOT NULL
              AND (k.aggregation_rule = 'sum' OR (t.status = 'ok' AND t.value IS NOT NULL))
        )::INTEGER AS cells_reported,
        COUNT(DISTINCT rc.cell_id) FILTER (
            WHERE k.aggregation_rule = 'traffic_weighted'
              AND v.status = 'ok' AND v.value IS NOT NULL
              AND t.status = 'ok' AND t.value > 0
        )::INTEGER AS cells_weighted,
        SUM(v.value) FILTER (
            WHERE k.aggregation_rule = 'sum' AND v.status = 'ok'
        ) AS sum_value,
        SUM(v.value * t.value) FILTER (
            WHERE k.aggregation_rule = 'traffic_weighted'
              AND v.status = 'ok' AND v.value IS NOT NULL
              AND t.status = 'ok' AND t.value > 0
        ) AS weighted_numerator,
        SUM(t.value) FILTER (
            WHERE k.aggregation_rule = 'traffic_weighted'
              AND v.status = 'ok' AND v.value IS NOT NULL
              AND t.status = 'ok' AND t.value > 0
        ) AS weighted_denominator,
        MAX(GREATEST(v.updated_at, COALESCE(t.updated_at, v.updated_at))) AS updated_at
    FROM region_cells rc
    JOIN cell_kpi_values v ON v.cell_id = rc.cell_id
    JOIN data_sources ds ON ds.source_id = v.source_id AND ds.is_active
    JOIN kpis k ON k.kpi_id = v.kpi_id AND k.is_active
    LEFT JOIN cell_kpi_values t
      ON t.source_id = v.source_id
     AND t.cell_id = v.cell_id
     AND t.period_start = v.period_start
     AND t.kpi_id = (SELECT kpi_id FROM traffic_kpi)
    GROUP BY rc.region_id, v.source_id, v.kpi_id, v.period_start
),
aggregated AS (
SELECT
    s.source_id, s.source_code, s.data_nature,
    s.region_id, s.region_code, s.region_name, s.region_level,
    s.kpi_id, s.kpi_code, s.kpi_name, s.unit, s.aggregation_rule,
    s.higher_is_better, s.is_quality_kpi,
    s.period_start,
    CASE
        WHEN s.aggregation_rule = 'sum' THEN kr.sum_value
        ELSE kr.weighted_numerator / NULLIF(kr.weighted_denominator, 0)
    END AS value,
    COALESCE(kr.cells_reported, 0)::INTEGER AS cells_reported,
    COALESCE(kr.cells_weighted, 0)::INTEGER AS cells_weighted,
    s.cells_total,
    CASE
        WHEN COALESCE(kr.cells_reported, 0) = 0 THEN 'missing'
        WHEN kr.cells_reported < s.cells_total THEN 'partial'
        ELSE 'ok'
    END AS status,
    CASE
        WHEN COALESCE(kr.cells_reported, 0) = 0 THEN 'no_input'
        WHEN s.aggregation_rule = 'sum' AND kr.sum_value IS NOT NULL THEN 'ok'
        WHEN s.aggregation_rule = 'sum' THEN 'no_input'
        WHEN COALESCE(kr.weighted_denominator, 0) > 0 THEN 'ok'
        ELSE 'no_positive_traffic'
    END AS aggregation_status,
    tr.traffic_total_gb,
    kr.weighted_denominator AS traffic_weight_gb,
    COALESCE(tr.traffic_cells_reported, 0)::INTEGER AS traffic_cells_reported,
    GREATEST(kr.updated_at, tr.traffic_updated_at) AS updated_at
FROM region_scope s
LEFT JOIN kpi_rollup kr
  ON kr.region_id = s.region_id
 AND kr.source_id = s.source_id
 AND kr.kpi_id = s.kpi_id
 AND kr.period_start = s.period_start
LEFT JOIN traffic_rollup tr
  ON tr.region_id = s.region_id
 AND tr.source_id = s.source_id
 AND tr.period_start = s.period_start
)
SELECT a.*, t.quality_level, t.threshold_type
FROM aggregated a
LEFT JOIN kpi_thresholds t
  ON t.kpi_id = a.kpi_id
 AND a.is_quality_kpi IS TRUE
 AND a.value IS NOT NULL
 AND a.value <@ numrange(t.min_value, t.max_value,
                          CASE WHEN a.higher_is_better THEN '[)' ELSE '(]' END);

-- ---------------------------------------------------------------------------
-- 8. VIEW v_region_kpi_daily: tong hop ngay theo lich Asia/Ho_Chi_Minh.
--    Phan loai threshold khi value IS NOT NULL, ke ca status='partial'.
--    Bien: KPI cang cao cang tot dung '[)' (>= min); cang thap cang tot dung '(]' (<= max).
--    Weighted value duoc tinh lai tu tat ca cell-hour hop le trong ngay.
--    status ngay dua tren cell_hours_reported / cell_hours_expected, khong
--    chi dua tren viec mot cell tung co it nhat mot gio du lieu.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_region_kpi_daily AS
WITH traffic_kpi AS (
    SELECT kpi_id FROM kpis WHERE kpi_code = 'traffic'
),
region_cells AS (
    SELECT r.region_id, c.cell_id
    FROM regions r
    JOIN cells c ON r.region_level = 'province' AND c.province_id = r.region_id AND c.is_active
    UNION ALL
    SELECT r.region_id, c.cell_id
    FROM regions r
    JOIN cells c ON r.region_level = 'ward' AND c.ward_id = r.region_id AND c.is_active
),
cell_counts AS (
    SELECT region_id, COUNT(*)::INTEGER AS cells_total
    FROM region_cells
    GROUP BY region_id
),
days AS (
    SELECT
        s.source_id, s.source_code, s.data_nature, s.timezone_name,
        g.local_day::DATE AS local_date,
        GREATEST(
            0,
            FLOOR(EXTRACT(EPOCH FROM (
                LEAST(s.period_to, ((g.local_day::DATE + 1)::TIMESTAMP AT TIME ZONE s.timezone_name))
                - GREATEST(s.period_from, (g.local_day::DATE::TIMESTAMP AT TIME ZONE s.timezone_name))
            )) / 3600)::INTEGER
        ) AS hours_expected
    FROM data_sources s
    CROSS JOIN LATERAL generate_series(
        (s.period_from AT TIME ZONE s.timezone_name)::DATE::TIMESTAMP,
        ((s.period_to - INTERVAL '1 microsecond') AT TIME ZONE s.timezone_name)::DATE::TIMESTAMP,
        INTERVAL '1 day'
    ) AS g(local_day)
    WHERE s.is_active
),
region_scope AS (
    SELECT
        d.source_id, d.source_code, d.data_nature, d.timezone_name,
        r.region_id, r.region_code, r.region_name, r.region_level,
        k.kpi_id, k.kpi_code, k.kpi_name, k.unit, k.aggregation_rule,
        k.higher_is_better, k.is_quality_kpi,
        d.local_date, d.hours_expected,
        COALESCE(cc.cells_total, 0)::INTEGER AS cells_total
    FROM days d
    CROSS JOIN regions r
    CROSS JOIN kpis k
    LEFT JOIN cell_counts cc ON cc.region_id = r.region_id
    WHERE k.is_active
),
traffic_rollup AS (
    SELECT
        rc.region_id,
        tv.source_id,
        (tv.period_start AT TIME ZONE ds.timezone_name)::DATE AS local_date,
        COUNT(DISTINCT rc.cell_id) FILTER (
            WHERE tv.status = 'ok' AND tv.value IS NOT NULL
        )::INTEGER AS traffic_cells_reported,
        SUM(tv.value) FILTER (
            WHERE tv.status = 'ok' AND tv.value IS NOT NULL
        ) AS traffic_total_gb,
        MAX(tv.updated_at) AS traffic_updated_at
    FROM region_cells rc
    JOIN cell_kpi_values tv ON tv.cell_id = rc.cell_id
    JOIN traffic_kpi tk ON tk.kpi_id = tv.kpi_id
    JOIN data_sources ds ON ds.source_id = tv.source_id AND ds.is_active
    GROUP BY rc.region_id, tv.source_id,
             (tv.period_start AT TIME ZONE ds.timezone_name)::DATE
),
kpi_rollup AS (
    SELECT
        rc.region_id, v.source_id, v.kpi_id,
        (v.period_start AT TIME ZONE ds.timezone_name)::DATE AS local_date,
        COUNT(DISTINCT rc.cell_id) FILTER (
            WHERE v.status = 'ok' AND v.value IS NOT NULL
              AND (k.aggregation_rule = 'sum' OR (t.status = 'ok' AND t.value IS NOT NULL))
        )::INTEGER AS cells_reported,
        COUNT(DISTINCT rc.cell_id) FILTER (
            WHERE k.aggregation_rule = 'traffic_weighted'
              AND v.status = 'ok' AND v.value IS NOT NULL
              AND t.status = 'ok' AND t.value > 0
        )::INTEGER AS cells_weighted,
        COUNT(*) FILTER (
            WHERE v.status = 'ok' AND v.value IS NOT NULL
              AND (k.aggregation_rule = 'sum' OR (t.status = 'ok' AND t.value IS NOT NULL))
        )::INTEGER AS cell_hours_reported,
        COUNT(*) FILTER (
            WHERE k.aggregation_rule = 'traffic_weighted'
              AND v.status = 'ok' AND v.value IS NOT NULL
              AND t.status = 'ok' AND t.value > 0
        )::INTEGER AS cell_hours_weighted,
        SUM(v.value) FILTER (
            WHERE k.aggregation_rule = 'sum' AND v.status = 'ok'
        ) AS sum_value,
        SUM(v.value * t.value) FILTER (
            WHERE k.aggregation_rule = 'traffic_weighted'
              AND v.status = 'ok' AND v.value IS NOT NULL
              AND t.status = 'ok' AND t.value > 0
        ) AS weighted_numerator,
        SUM(t.value) FILTER (
            WHERE k.aggregation_rule = 'traffic_weighted'
              AND v.status = 'ok' AND v.value IS NOT NULL
              AND t.status = 'ok' AND t.value > 0
        ) AS weighted_denominator,
        MAX(GREATEST(v.updated_at, COALESCE(t.updated_at, v.updated_at))) AS updated_at
    FROM region_cells rc
    JOIN cell_kpi_values v ON v.cell_id = rc.cell_id
    JOIN data_sources ds ON ds.source_id = v.source_id AND ds.is_active
    JOIN kpis k ON k.kpi_id = v.kpi_id AND k.is_active
    LEFT JOIN cell_kpi_values t
      ON t.source_id = v.source_id
     AND t.cell_id = v.cell_id
     AND t.period_start = v.period_start
     AND t.kpi_id = (SELECT kpi_id FROM traffic_kpi)
    GROUP BY rc.region_id, v.source_id, v.kpi_id,
             (v.period_start AT TIME ZONE ds.timezone_name)::DATE
),
aggregated AS (
SELECT
    s.source_id, s.source_code, s.data_nature,
    s.region_id, s.region_code, s.region_name, s.region_level,
    s.kpi_id, s.kpi_code, s.kpi_name, s.unit, s.aggregation_rule,
    s.higher_is_better, s.is_quality_kpi,
    s.local_date,
    CASE
        WHEN s.aggregation_rule = 'sum' THEN kr.sum_value
        ELSE kr.weighted_numerator / NULLIF(kr.weighted_denominator, 0)
    END AS value,
    COALESCE(kr.cells_reported, 0)::INTEGER AS cells_reported,
    COALESCE(kr.cells_weighted, 0)::INTEGER AS cells_weighted,
    s.cells_total,
    CASE
        WHEN COALESCE(kr.cell_hours_reported, 0) = 0 THEN 'missing'
        WHEN kr.cell_hours_reported < (s.cells_total * s.hours_expected) THEN 'partial'
        ELSE 'ok'
    END AS status,
    CASE
        WHEN COALESCE(kr.cell_hours_reported, 0) = 0 THEN 'no_input'
        WHEN s.aggregation_rule = 'sum' AND kr.sum_value IS NOT NULL THEN 'ok'
        WHEN s.aggregation_rule = 'sum' THEN 'no_input'
        WHEN COALESCE(kr.weighted_denominator, 0) > 0 THEN 'ok'
        ELSE 'no_positive_traffic'
    END AS aggregation_status,
    COALESCE(kr.cell_hours_reported, 0)::INTEGER AS cell_hours_reported,
    COALESCE(kr.cell_hours_weighted, 0)::INTEGER AS cell_hours_weighted,
    (s.cells_total * s.hours_expected)::INTEGER AS cell_hours_expected,
    tr.traffic_total_gb,
    kr.weighted_denominator AS traffic_weight_gb,
    COALESCE(tr.traffic_cells_reported, 0)::INTEGER AS traffic_cells_reported,
    GREATEST(kr.updated_at, tr.traffic_updated_at) AS updated_at
FROM region_scope s
LEFT JOIN kpi_rollup kr
  ON kr.region_id = s.region_id
 AND kr.source_id = s.source_id
 AND kr.kpi_id = s.kpi_id
 AND kr.local_date = s.local_date
LEFT JOIN traffic_rollup tr
  ON tr.region_id = s.region_id
 AND tr.source_id = s.source_id
 AND tr.local_date = s.local_date
)
SELECT a.*, t.quality_level, t.threshold_type
FROM aggregated a
LEFT JOIN kpi_thresholds t
  ON t.kpi_id = a.kpi_id
 AND a.is_quality_kpi IS TRUE
 AND a.value IS NOT NULL
 AND a.value <@ numrange(t.min_value, t.max_value,
                          CASE WHEN a.higher_is_better THEN '[)' ELSE '(]' END);

-- ---------------------------------------------------------------------------
-- 9. VIEW kiem tra threshold.
--    Chi con 2 view nghiep vu; moi view da LEFT JOIN threshold.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_kpi_threshold_check AS
WITH p AS (
    SELECT k.kpi_code, k.higher_is_better,
           MAX(t.min_value) FILTER (WHERE t.quality_level = 'good') AS good_min,
           MAX(t.max_value) FILTER (WHERE t.quality_level = 'good') AS good_max,
           MAX(t.min_value) FILTER (WHERE t.quality_level = 'medium') AS med_min,
           MAX(t.max_value) FILTER (WHERE t.quality_level = 'medium') AS med_max,
           MAX(t.min_value) FILTER (WHERE t.quality_level = 'poor') AS poor_min,
           MAX(t.max_value) FILTER (WHERE t.quality_level = 'poor') AS poor_max,
           COUNT(t.threshold_id) AS levels
    FROM kpis k
    LEFT JOIN kpi_thresholds t ON t.kpi_id = k.kpi_id
    WHERE k.is_active AND k.is_quality_kpi
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

-- ---------------------------------------------------------------------------
-- 10. DU LIEU KHOI TAO: 4 KPI va nguon mo phong 30 ngay (Traffic dung GB thap phan).
--     Gia tri cell/hour se do Data/QA nap sau; script KHONG tao KPI gia.
-- ---------------------------------------------------------------------------
INSERT INTO kpis
(kpi_code, kpi_name, kpi_group, unit, higher_is_better, is_quality_kpi, is_ratio,
 aggregation_rule, valid_min, valid_max, description, calculation_method, reference_name, display_order)
VALUES
('cssr', 'Call Setup Success Rate (CSSR / A1)', 'accessibility', '%', TRUE, TRUE, TRUE,
 'traffic_weighted', 0, 100,
 'Ty le thiet lap E-RAB ban dau thanh cong tai cap cell. Mentor su dung ten CSSR; 3GPP TS 32.450 V19.0.0 (2025-10) goi chi so tuong ung la A1 - Initial E-RAB establishment success rate.',
 'CSSR (%) = (SUM(RRC.ConnEstabSucc) / SUM(RRC.ConnEstabAtt)) x (S1SIG.ConnEstabSucc / S1SIG.ConnEstabAtt) x (SUM(ERAB.EstabInitSuccNbr) / SUM(ERAB.EstabInitAttNbr)) x 100. Cac ty so thanh phan duoc hieu la ty le thap phan. Tham chieu 3GPP TS 32.450 V19.0.0 (2025-10), clause 6.1.1, A1 - Initial E-RAB establishment success rate. Du lieu mo phong sinh truc tiep gia tri KPI cuoi cung o cap cell/gio; khong luu counter trong CSDL.',
 '3GPP TS 32.450 V19.0.0 (2025-10), clause 6.1.1, A1 - Initial E-RAB establishment success rate; CSSR la ten Mentor su dung cho chi so nay.', 1),
('service_drop_all', 'Service Drop All', 'retainability', '%', FALSE, TRUE, TRUE,
 'traffic_weighted', 0, 100,
 'Ty le E-RAB giai phong bat thuong trong khi van con du lieu trong buffer tren tong so E-RAB giai phong; day la dinh nghia van hanh du an su dung.',
 'Service Drop All (%) = so E-RAB giai phong bat thuong khi con du lieu trong buffer / tong so E-RAB giai phong x 100. DAY KHONG PHAI cong thuc do 3GPP quy dinh; la cong thuc de xuat theo thuc tien van hanh, dang cho Mentor VNPT xac nhan. 3GPP TS 32.450 V19.0.0 (2025-10), clause 6.2.1 dinh nghia E-RAB Retainability theo so lan giai phong bat thuong tren thoi gian phien E-RAB (events/second), la chi so khac. Neu tong so E-RAB giai phong bang 0 thi gia tri KPI khong xac dinh va phai duoc sinh voi status=missing, value=NULL. Du lieu mo phong sinh truc tiep gia tri KPI o cap cell/gio; khong luu counter trong CSDL.',
 'Cong thuc de xuat theo thuc tien van hanh, khong phai cong thuc 3GPP; dang cho Mentor VNPT xac nhan cach tinh VNPT su dung. Tham chieu de phan biet: 3GPP TS 32.450 V19.0.0 (2025-10), clause 6.2.1 ve E-RAB Retainability.', 2),
('user_throughput', 'User Throughput (Downlink)', 'user_performance', 'Mbps', TRUE, TRUE, FALSE,
 'traffic_weighted', 0, NULL,
 'Thong luong nguoi dung tai xuong tai cap cell, luu theo Mbps.',
 'Theo 3GPP TS 32.450 V19.0.0 (2025-10), clause 6.3.1: User Throughput (kbit/s) = ThpVolDl / ThpTimeDl. Schema luu Mbps = (ThpVolDl / ThpTimeDl) / 1000. Du lieu mo phong sinh truc tiep gia tri KPI cuoi cung o cap cell/gio (don vi Mbps); khong luu counter trong CSDL.',
 '3GPP TS 32.450 V19.0.0 (2025-10), clause 6.3.1; ThpVolDl / ThpTimeDl, quy doi kbit/s sang Mbps bang cach chia 1000.', 3),
('traffic', 'Traffic Volume', 'traffic', 'GB', NULL, FALSE, FALSE,
 'sum', 0, NULL,
 'Tong luong traffic cua cell trong cung mot gio, don vi GB thap phan (1 GB = 10^9 byte); dung lam trong so cho cac KPI chat luong.',
 'Luu truc tiep gia tri Traffic cua cell trong mot gio, don vi GB thap phan (1 GB = 10^9 byte); khong dung GiB. Tong hop len phuong/tinh bang phep cong SUM. Du lieu mo phong sinh truc tiep gia tri KPI o cap cell/gio; khong luu counter trong CSDL.',
 'Quy uoc don vi du an: GB thap phan (10^9 byte); KPI dictionary / nguon du lieu can ghi ro don vi goc neu co.', 4)
ON CONFLICT (kpi_code) DO UPDATE SET
    kpi_name = EXCLUDED.kpi_name,
    kpi_group = EXCLUDED.kpi_group,
    unit = EXCLUDED.unit,
    higher_is_better = EXCLUDED.higher_is_better,
    is_quality_kpi = EXCLUDED.is_quality_kpi,
    is_ratio = EXCLUDED.is_ratio,
    aggregation_rule = EXCLUDED.aggregation_rule,
    valid_min = EXCLUDED.valid_min,
    valid_max = EXCLUDED.valid_max,
    description = EXCLUDED.description,
    calculation_method = EXCLUDED.calculation_method,
    reference_name = EXCLUDED.reference_name,
    display_order = EXCLUDED.display_order,
    is_active = TRUE;

INSERT INTO data_sources
(source_code, source_name, source_type, data_nature, description, spatial_scope,
 period_from, period_to, timezone_name, collection_method, method_version, random_seed,
 assumptions, limitations, source_url, is_default, is_active)
VALUES
('SIM-4G-2026-10', 'Bo du lieu mo phong mang di dong 4G - 30 ngay',
 'simulation', 'simulated',
 'Bo KPI 4G cap cell theo gio cho giai doan 30 ngay; Traffic dung GB thap phan (10^9 byte); phuc vu demo ban do giam sat.',
 '34 tinh/thanh tren toan quoc; cap phuong/xa chi TP.HCM (168 don vi); khoang 1.000 cell; giai doan 1 chi nap RAT 4G.',
 TIMESTAMPTZ '2026-10-01 00:00:00+07',
 TIMESTAMPTZ '2026-10-31 00:00:00+07',
 'Asia/Ho_Chi_Minh',
 'PLACEHOLDER: Data/QA phai ghi ro thuat toan, tham so, phan bo va cach kiem tra tinh hop ly truoc khi nap du lieu KPI.',
 'v1', 20261119,
 'Danh sach cell va trang thai is_active duoc coi la co dinh trong 30 ngay; Data/QA bo sung gia dinh mo phong cu the (phan bo tai, bien dong theo gio, phan bo KPI theo cell), seed va phuong phap tai day.',
 'Khong phai so lieu do thuc te cua VNPT; khong dung de ket luan hien trang chat luong mang thuc te. is_active khong phan anh bat/tat cell giua ky; cell roster duoc gia dinh co dinh trong 30 ngay.',
 NULL, TRUE, TRUE)
ON CONFLICT (source_code) DO UPDATE SET
    source_name = EXCLUDED.source_name,
    source_type = EXCLUDED.source_type,
    data_nature = EXCLUDED.data_nature,
    description = EXCLUDED.description,
    spatial_scope = EXCLUDED.spatial_scope,
    period_from = EXCLUDED.period_from,
    period_to = EXCLUDED.period_to,
    timezone_name = EXCLUDED.timezone_name,
    collection_method = EXCLUDED.collection_method,
    method_version = EXCLUDED.method_version,
    random_seed = EXCLUDED.random_seed,
    assumptions = EXCLUDED.assumptions,
    limitations = EXCLUDED.limitations,
    source_url = EXCLUDED.source_url,
    is_default = EXCLUDED.is_default,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- 11. MATERIALIZED VIEWS: ket qua tong hop san cho API.
--     View goc van la nguon logic/chuan de doi chieu.
--     API doc tu materialized views sau khi da REFRESH.
--     Tao WITH DATA de MV o trang thai populated (co the rong neu chua nap
--     regions/cells); bat buoc REFRESH lai sau khi nap du lieu va threshold.
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_region_kpi AS
SELECT * FROM v_region_kpi
WITH DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_region_kpi_daily AS
SELECT * FROM v_region_kpi_daily
WITH DATA;

-- Index cho truy van mot KPI / cap region / mot moc thoi gian.
CREATE INDEX IF NOT EXISTS mv_region_kpi_kpi_level_time_idx
ON mv_region_kpi (kpi_code, region_level, period_start);

CREATE INDEX IF NOT EXISTS mv_region_kpi_region_kpi_time_idx
ON mv_region_kpi (region_code, kpi_code, period_start);

CREATE INDEX IF NOT EXISTS mv_region_kpi_daily_kpi_level_date_idx
ON mv_region_kpi_daily (kpi_code, region_level, local_date);

CREATE INDEX IF NOT EXISTS mv_region_kpi_daily_region_kpi_date_idx
ON mv_region_kpi_daily (region_code, kpi_code, local_date);

COMMENT ON MATERIALIZED VIEW mv_region_kpi IS
'Tong hop KPI theo gio; refresh sau khi nap/cap nhat cell_kpi_values, cells, data_sources hoac kpi_thresholds.';
COMMENT ON MATERIALIZED VIEW mv_region_kpi_daily IS
'Tong hop KPI theo ngay Asia/Ho_Chi_Minh; refresh sau khi nap/cap nhat cell_kpi_values, cells, data_sources hoac kpi_thresholds.';

-- ---------------------------------------------------------------------------
-- 12. HUONG DAN NAP DU LIEU HANH CHINH VA CELL (thuc hien rieng)
-- ---------------------------------------------------------------------------
-- A. Nap 34 province truoc, sau do nap 168 ward/commune cua TP.HCM.
--    Nguon GeoJSON tham khao: https://huggingface.co/datasets/myleo198/sapnhap-bando-vn
--    Giay phep hien thi tren Hugging Face: CC BY-NC 4.0 (ghi attribution; khong dung thuong mai).
--    Nguon du phong: GitHub thanglequoc/vietnamese-provinces-database;
--    can kiem tra lai do cap nhat va giay phep truoc khi thay nguon chinh.
--    Can map: ma -> region_code; ten -> region_name; geom -> geometry(MultiPolygon,4326).
--    ward.parent_region_id tro den province.region_id.
-- B. Nap cells: cell_code, province_id bat buoc, ward_id (neu co), rat='4G' trong giai doan 1.
--    Khong nap toa do tram/cell. province_id bat buoc; ward_id nullable cho pham vi
--    chi co du lieu cap tinh. Cell tai TP.HCM gan ward_id de co the tong hop cap phuong.
-- C. Nap cell_kpi_values: moi cell x KPI x gio x nguon mot dong; khong nap counter.
-- D. Schema co ten co dinh n46; so phien ban chi nam trong tai lieu va ten file SQL N4.6_Database_Schema.sql.
-- E. Hai view nghiep vu da LEFT JOIN kpi_thresholds de tra quality_level/threshold_type.
--    View giu status va aggregation_status; API map ve status (ok/partial/missing).
--    Neu aggregation_status='no_positive_traffic',
--    API tra value=NULL va reason='no_positive_traffic'. Day la mapping API, khong phai cot moi trong DB.
-- F. Sau khi nap xong GeoJSON, cells, cell_kpi_values va thresholds:
--    REFRESH MATERIALIZED VIEW n46.mv_region_kpi;
--    REFRESH MATERIALIZED VIEW n46.mv_region_kpi_daily;
--    ANALYZE n46.mv_region_kpi;
--    ANALYZE n46.mv_region_kpi_daily;
--    Refresh khong chay tu dong. Neu cap nhat du lieu/threshold sau nay, chay lai.
-- G. API nen doc tu MV; view goc dung de doi chieu/kiem thu:
--    SELECT * FROM n46.mv_region_kpi WHERE kpi_code='cssr' AND period_start='2026-10-01 08:00:00+07';
--    SELECT * FROM n46.mv_region_kpi_daily WHERE kpi_code='user_throughput' AND local_date='2026-10-01';
-- ---------------------------------------------------------------------------

COMMIT;
