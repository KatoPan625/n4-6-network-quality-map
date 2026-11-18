"""API doc gia tri KPI (schema V2.1). Khong phu thuoc KPI cu the: danh sach KPI lay tu bang kpis.

Gia tri doc tu view v_kpi_values_classified (da kem quality_level va data_nature).
"""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(prefix="/api/v1", tags=["kpi"])
SessionDep = Annotated[Session, Depends(get_session)]
PeriodType = Literal["week"]  # V2.1 chi co chu ky tuan (thu Hai - Chu nhat)
RegionFilter = Annotated[list[str] | None, Query(description="Loc theo ma o, lap duoc")]
SourceParam = Annotated[
    str | None, Query(description="Ma nguon du lieu; bo trong = nguon mac dinh (is_default)")
]

# O khong co dong du lieu cho tuan dang hoi -> tra status "missing", value null (khong phai 0)
REGION_FILTER_SQL = "(CAST(:regions AS text[]) IS NULL OR r.region_code = ANY(:regions))"
VALUE_COLS = "value::float8 AS value, status, sample_count, quality_level, threshold_type"


def get_kpi(session: Session, code: str) -> dict:
    row = (
        session.execute(
            text(
                "SELECT kpi_code, unit, higher_is_better FROM kpis WHERE kpi_code = :c AND is_active"
            ),
            {"c": code},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"KPI '{code}' khong ton tai")
    return dict(row)


def get_source(session: Session, code: str | None) -> dict:
    row = (
        session.execute(
            text(
                "SELECT source_code, source_name, data_nature FROM data_sources "
                "WHERE (CAST(:c AS text) IS NULL AND is_default) OR source_code = :c"
            ),
            {"c": code},
        )
        .mappings()
        .first()
    )
    if row is None:
        detail = f"Nguon '{code}' khong ton tai" if code else "Chua co nguon mac dinh"
        raise HTTPException(status_code=404, detail=detail)
    return dict(row)


def check_monday(*days: date | None) -> None:
    for d in days:
        if d is not None and d.isoweekday() != 1:
            raise HTTPException(status_code=422, detail=f"{d} khong phai thu Hai (dau tuan)")


@router.get("/kpi-values")
def kpi_values(
    session: SessionDep,
    kpi: str,
    period_start: date,
    period_type: PeriodType = "week",
    region: RegionFilter = None,
    source: SourceParam = None,
) -> dict:
    """Gia tri 1 KPI cua moi o trong 1 tuan - dung de to mau ban do."""
    check_monday(period_start)
    k = get_kpi(session, kpi)
    s = get_source(session, source)
    rows = session.execute(
        text(
            "SELECT r.region_code, v.value::float8 AS value, "
            "COALESCE(v.status, 'missing') AS status, COALESCE(v.sample_count, 0) AS sample_count, "
            "v.quality_level, v.threshold_type "
            "FROM regions r LEFT JOIN v_kpi_values_classified v "
            "ON v.region_code = r.region_code AND v.kpi_code = :kpi "
            "AND v.source_code = :src AND v.period_start = :ps "
            f"WHERE {REGION_FILTER_SQL} ORDER BY r.region_code"
        ),
        {"kpi": kpi, "src": s["source_code"], "ps": period_start, "regions": region},
    ).mappings()
    return {
        "kpi": k,
        "source": s,
        "period": {"type": period_type, "start": period_start},
        "items": [dict(r) for r in rows],
    }


@router.get("/regions/{region_code}/kpis")
def region_kpis(
    session: SessionDep,
    region_code: str,
    kpi: str | None = None,
    period_type: PeriodType = "week",
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    source: SourceParam = None,
) -> dict:
    """Chuoi thoi gian KPI cua 1 o - dung cho man hinh chi tiet."""
    if from_ and to and from_ > to:
        raise HTTPException(status_code=422, detail="'from' phai nho hon hoac bang 'to'")
    found = session.execute(
        text("SELECT 1 FROM regions WHERE region_code = :rc"), {"rc": region_code}
    ).first()
    if found is None:
        raise HTTPException(status_code=404, detail=f"O '{region_code}' khong ton tai")
    if kpi:
        get_kpi(session, kpi)
    s = get_source(session, source)
    rows = session.execute(
        text(
            f"SELECT k.kpi_code, k.kpi_name, k.unit, v.period_start, {VALUE_COLS} "
            "FROM v_kpi_values_classified v JOIN kpis k USING (kpi_code) "
            "WHERE v.region_code = :rc AND v.source_code = :src "
            "AND (CAST(:kpi AS text) IS NULL OR v.kpi_code = :kpi) "
            "AND (CAST(:f AS date) IS NULL OR v.period_start >= :f) "
            "AND (CAST(:t AS date) IS NULL OR v.period_start <= :t) "
            "ORDER BY k.display_order, v.period_start"
        ),
        {"rc": region_code, "src": s["source_code"], "kpi": kpi, "f": from_, "t": to},
    ).mappings()
    kpis: dict[str, dict] = {}
    point_keys = (
        "period_start",
        "value",
        "status",
        "sample_count",
        "quality_level",
        "threshold_type",
    )
    for r in rows:
        entry = kpis.setdefault(
            r["kpi_code"],
            {"kpi_code": r["kpi_code"], "kpi_name": r["kpi_name"], "unit": r["unit"], "series": []},
        )
        entry["series"].append({k: r[k] for k in point_keys})
    return {
        "region_code": region_code,
        "source": s,
        "period_type": period_type,
        "kpis": list(kpis.values()),
    }


@router.get("/compare")
def compare(
    session: SessionDep,
    kpi: str,
    period_a: date,
    period_b: date,
    period_type: PeriodType = "week",
    region: RegionFilter = None,
    source: SourceParam = None,
) -> dict:
    """So sanh 1 KPI giua 2 tuan. delta = B - A; null neu 1 trong 2 tuan thieu du lieu."""
    check_monday(period_a, period_b)
    k = get_kpi(session, kpi)
    s = get_source(session, source)
    rows = session.execute(
        text(
            "SELECT r.region_code, "
            "a.value::float8 AS value_a, COALESCE(a.status, 'missing') AS status_a, "
            "a.quality_level AS quality_level_a, "
            "b.value::float8 AS value_b, COALESCE(b.status, 'missing') AS status_b, "
            "b.quality_level AS quality_level_b "
            "FROM regions r "
            "LEFT JOIN v_kpi_values_classified a ON a.region_code = r.region_code "
            "AND a.kpi_code = :kpi AND a.source_code = :src AND a.period_start = :pa "
            "LEFT JOIN v_kpi_values_classified b ON b.region_code = r.region_code "
            "AND b.kpi_code = :kpi AND b.source_code = :src AND b.period_start = :pb "
            f"WHERE {REGION_FILTER_SQL} ORDER BY r.region_code"
        ),
        {"kpi": kpi, "src": s["source_code"], "pa": period_a, "pb": period_b, "regions": region},
    ).mappings()
    items = []
    for r in rows:
        item = dict(r)
        both = r["value_a"] is not None and r["value_b"] is not None
        item["delta"] = round(r["value_b"] - r["value_a"], 4) if both else None
        items.append(item)
    return {
        "kpi": k,
        "source": s,
        "period_type": period_type,
        "period_a": period_a,
        "period_b": period_b,
        "items": items,
    }
