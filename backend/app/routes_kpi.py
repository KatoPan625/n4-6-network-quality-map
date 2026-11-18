"""API doc gia tri KPI. Khong phu thuoc KPI cu the: danh sach KPI lay tu bang kpi_definition."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(prefix="/api/v1", tags=["kpi"])
SessionDep = Annotated[Session, Depends(get_session)]
PeriodType = Literal["day", "week", "month"]
RegionFilter = Annotated[list[str] | None, Query(description="Loc theo ma vung, lap duoc")]

# Vung khong co dong du lieu cho ky dang hoi -> tra status "missing", value null (khong phai 0)
REGION_FILTER_SQL = "(CAST(:regions AS text[]) IS NULL OR r.region_code = ANY(:regions))"


def get_kpi(session: Session, code: str) -> dict:
    row = session.execute(
        text("SELECT code, name, unit, higher_is_better FROM kpi_definition WHERE code = :c"),
        {"c": code},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"KPI '{code}' khong ton tai")
    return dict(row)


@router.get("/kpi-values")
def kpi_values(
    session: SessionDep,
    kpi: str,
    period_start: date,
    period_type: PeriodType = "month",
    region: RegionFilter = None,
) -> dict:
    """Gia tri 1 KPI cua moi vung trong 1 ky - dung de to mau ban do."""
    k = get_kpi(session, kpi)
    rows = session.execute(
        text(
            "SELECT r.region_code, v.value, COALESCE(v.status, 'missing') AS status, "
            "v.updated_at FROM region r LEFT JOIN kpi_value v "
            "ON v.region_code = r.region_code AND v.kpi_code = :kpi "
            "AND v.period_type = :pt AND v.period_start = :ps "
            f"WHERE {REGION_FILTER_SQL} ORDER BY r.region_code"
        ),
        {"kpi": kpi, "pt": period_type, "ps": period_start, "regions": region},
    ).mappings()
    return {
        "kpi": {"code": k["code"], "unit": k["unit"], "higher_is_better": k["higher_is_better"]},
        "period": {"type": period_type, "start": period_start},
        "items": [dict(r) for r in rows],
    }


@router.get("/regions/{region_code}/kpis")
def region_kpis(
    session: SessionDep,
    region_code: str,
    kpi: str | None = None,
    period_type: PeriodType = "month",
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
) -> dict:
    """Chuoi thoi gian KPI cua 1 vung - dung cho man hinh chi tiet."""
    if from_ and to and from_ > to:
        raise HTTPException(status_code=422, detail="'from' phai nho hon hoac bang 'to'")
    found = session.execute(
        text("SELECT 1 FROM region WHERE region_code = :rc"), {"rc": region_code}
    ).first()
    if found is None:
        raise HTTPException(status_code=404, detail=f"Vung '{region_code}' khong ton tai")
    if kpi:
        get_kpi(session, kpi)
    rows = session.execute(
        text(
            "SELECT d.code, d.name, d.unit, v.period_start, v.value, v.status, v.updated_at "
            "FROM kpi_value v JOIN kpi_definition d ON d.code = v.kpi_code "
            "WHERE v.region_code = :rc AND v.period_type = :pt "
            "AND (CAST(:kpi AS text) IS NULL OR v.kpi_code = :kpi) "
            "AND (CAST(:f AS date) IS NULL OR v.period_start >= :f) "
            "AND (CAST(:t AS date) IS NULL OR v.period_start <= :t) "
            "ORDER BY d.code, v.period_start"
        ),
        {"rc": region_code, "pt": period_type, "kpi": kpi, "f": from_, "t": to},
    ).mappings()
    kpis: dict[str, dict] = {}
    for r in rows:
        entry = kpis.setdefault(
            r["code"], {"code": r["code"], "name": r["name"], "unit": r["unit"], "series": []}
        )
        entry["series"].append(
            {k: r[k] for k in ("period_start", "value", "status", "updated_at")}
        )
    return {"region_code": region_code, "period_type": period_type, "kpis": list(kpis.values())}


@router.get("/compare")
def compare(
    session: SessionDep,
    kpi: str,
    period_a: date,
    period_b: date,
    period_type: PeriodType = "month",
    region: RegionFilter = None,
) -> dict:
    """So sanh 1 KPI giua 2 ky. delta = B - A; null neu 1 trong 2 ky thieu du lieu."""
    k = get_kpi(session, kpi)
    rows = session.execute(
        text(
            "SELECT r.region_code, a.value AS value_a, COALESCE(a.status, 'missing') AS status_a, "
            "b.value AS value_b, COALESCE(b.status, 'missing') AS status_b "
            "FROM region r "
            "LEFT JOIN kpi_value a ON a.region_code = r.region_code AND a.kpi_code = :kpi "
            "AND a.period_type = :pt AND a.period_start = :pa "
            "LEFT JOIN kpi_value b ON b.region_code = r.region_code AND b.kpi_code = :kpi "
            "AND b.period_type = :pt AND b.period_start = :pb "
            f"WHERE {REGION_FILTER_SQL} ORDER BY r.region_code"
        ),
        {"kpi": kpi, "pt": period_type, "pa": period_a, "pb": period_b, "regions": region},
    ).mappings()
    items = []
    for r in rows:
        item = dict(r)
        both = r["value_a"] is not None and r["value_b"] is not None
        item["delta"] = round(r["value_b"] - r["value_a"], 4) if both else None
        items.append(item)
    return {
        "kpi": {"code": k["code"], "unit": k["unit"], "higher_is_better": k["higher_is_better"]},
        "period_type": period_type,
        "period_a": period_a,
        "period_b": period_b,
        "items": items,
    }
