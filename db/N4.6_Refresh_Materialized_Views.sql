-- N4.6: refresh precomputed regional KPI results.
-- Run only AFTER importing/updating regions, cells, cell_kpi_values,
-- data_sources and kpi_thresholds.
-- Refresh is intentionally non-CONCURRENTLY: simulated data is loaded in batch
-- and a full refresh is performed once after the load.

REFRESH MATERIALIZED VIEW n46.mv_region_kpi;
REFRESH MATERIALIZED VIEW n46.mv_region_kpi_daily;

ANALYZE n46.mv_region_kpi;
ANALYZE n46.mv_region_kpi_daily;
