-- BAN NHAP de Backend test. Schema chinh thuc do Lead (Dat) chu tri.
-- Chi luu vung tong hop / o luoi gia lap, KHONG luu toa do tram hay thue bao.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE region (
    region_code TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    level       TEXT NOT NULL,                      -- vd: grid, district, province
    geom        geometry(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX region_geom_gix ON region USING GIST (geom);

-- Metadata KPI: API doc tu day, khong hard-code danh sach KPI
CREATE TABLE kpi_definition (
    code             TEXT PRIMARY KEY,               -- vd: latency_ms
    name             TEXT NOT NULL,
    unit             TEXT NOT NULL,
    description      TEXT NOT NULL,                  -- cach tinh
    higher_is_better BOOLEAN NOT NULL
);

CREATE TABLE kpi_value (
    region_code  TEXT NOT NULL REFERENCES region(region_code),
    kpi_code     TEXT NOT NULL REFERENCES kpi_definition(code),
    period_type  TEXT NOT NULL CHECK (period_type IN ('day', 'week', 'month')),
    period_start DATE NOT NULL,
    value        DOUBLE PRECISION,                   -- NULL khi thieu du lieu
    status       TEXT NOT NULL CHECK (status IN ('ok', 'missing', 'invalid')),
    source       TEXT NOT NULL,                      -- vd: simulated-v1
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (region_code, kpi_code, period_type, period_start),
    CHECK ((status = 'ok' AND value IS NOT NULL) OR (status <> 'ok' AND value IS NULL))
);
CREATE INDEX kpi_value_lookup_idx ON kpi_value (kpi_code, period_type, period_start);
