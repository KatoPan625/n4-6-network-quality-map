"""API doc gia tri KPI theo vung. Doc tu 2 materialized view mv_region_kpi (gio)
va mv_region_kpi_daily (ngay); danh sach KPI lay tu bang kpis, khong viet cung.
"""

from datetime import date, datetime, timedelta
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(prefix="/api/v1", tags=["kpi"])
SessionDep = Annotated[Session, Depends(get_session)]
VN = ZoneInfo("Asia/Ho_Chi_Minh")

PeriodType = Literal["hour", "day"]
Level = Literal["province", "ward"]
RegionFilter = Annotated[list[str] | None, Query(description="Loc theo ma vung, lap duoc")]
SourceParam = Annotated[
    str | None, Query(description="Ma nguon du lieu; bo trong = nguon mac dinh (is_default)")
]
AtDesc = "hour: 'YYYY-MM-DDTHH:00' (gio VN, co the kem +07:00); day: 'YYYY-MM-DD'"

# period_type -> (materialized view, cot thoi gian, cot rieng cua ban ngay)
MV = {
    "hour": ("mv_region_kpi", "period_start", ""),
    "day": ("mv_region_kpi_daily", "local_date", ", cell_hours_reported, cell_hours_expected"),
}
POINT_COLS = (
    "value::float8 AS value, status, aggregation_status, "
    "quality_level, threshold_type, cells_reported, cells_total, updated_at"
)


def region_filter(col: str = "region_code") -> str:
    return f"(CAST(:regions AS text[]) IS NULL OR {col} = ANY(:regions))"


def get_kpi(session: Session, code: str) -> dict:
    row = (
        session.execute(
            text(
                "SELECT kpi_code, kpi_name, unit, higher_is_better, aggregation_rule FROM kpis "
                "WHERE kpi_code = :c AND is_active"
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
                "SELECT source_code, source_name, data_nature, period_from, period_to "
                "FROM data_sources WHERE is_active "
                "AND ((CAST(:c AS text) IS NULL AND is_default) OR source_code = :c)"
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


def parse_at(period_type: PeriodType, raw: str, source: dict) -> datetime | date:
    """Doc moc thoi gian va kiem tra nam trong khoang du lieu cua nguon."""
    raw = raw.strip().replace(" ", "+")  # '+' trong query string bi doi thanh dau cach
    try:
        at = date.fromisoformat(raw) if period_type == "day" else datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"'{raw}' sai dinh dang. {AtDesc}") from exc
    start, end = source["period_from"], source["period_to"]
    if period_type == "day":
        first = start.astimezone(VN).date()
        last = (end - timedelta(microseconds=1)).astimezone(VN).date()
        inside = first <= at <= last
    else:
        at = (at if at.tzinfo else at.replace(tzinfo=VN)).astimezone(VN)
        if at.minute or at.second or at.microsecond:
            raise HTTPException(status_code=422, detail=f"'{raw}' phai dung dau gio (gio VN)")
        inside = start <= at < end
    if not inside:
        raise HTTPException(
            status_code=422,
            detail=f"'{raw}' nam ngoai khoang du lieu cua nguon {source['source_code']}",
        )
    return at


def to_item(row) -> dict:
    """status giu ok/partial/missing; aggregation_status chi lo ra qua 'reason'."""
    item = dict(row)
    agg = item.pop("aggregation_status")
    item["reason"] = agg if agg == "no_positive_traffic" else None
    return item


@router.get("/kpi-values")
def kpi_values(
    session: SessionDep,
    kpi: str,
    at: Annotated[str, Query(description=AtDesc)],
    level: Level = "province",
    period_type: PeriodType = "hour",
    region: RegionFilter = None,
    source: SourceParam = None,
) -> dict:
    """Gia tri 1 KPI cua moi vung o 1 gio hoac 1 ngay - dung de to mau ban do."""
    k = get_kpi(session, kpi)
    s = get_source(session, source)
    moment = parse_at(period_type, at, s)
    view, tcol, extra = MV[period_type]
    rows = session.execute(
        text(
            f"SELECT region_code, region_name, {POINT_COLS}{extra} FROM {view} "
            "WHERE source_code = :src AND kpi_code = :kpi AND region_level = :lvl "
            f"AND {tcol} = :at AND {region_filter()} ORDER BY region_code"
        ),
        {"src": s["source_code"], "kpi": kpi, "lvl": level, "at": moment, "regions": region},
    ).mappings()
    return {
        "kpi": k,
        "source": s,
        "level": level,
        "period": {"type": period_type, "at": moment},
        "items": [to_item(r) for r in rows],
    }


@router.get("/regions/{region_code}/kpis")
def region_kpis(
    session: SessionDep,
    region_code: str,
    kpi: str | None = None,
    period_type: PeriodType = "day",
    from_: Annotated[str | None, Query(alias="from", description=AtDesc)] = None,
    to: Annotated[str | None, Query(description=AtDesc)] = None,
    source: SourceParam = None,
) -> dict:
    """Chuoi thoi gian KPI cua 1 vung - dung cho man hinh chi tiet. Mac dinh ca khoang cua nguon."""
    region = (
        session.execute(
            text(
                "SELECT r.region_code, r.region_name, r.region_level, p.region_code AS parent_code "
                "FROM regions r LEFT JOIN regions p ON p.region_id = r.parent_region_id "
                "WHERE r.region_code = :rc"
            ),
            {"rc": region_code},
        )
        .mappings()
        .first()
    )
    if region is None:
        raise HTTPException(status_code=404, detail=f"Vung '{region_code}' khong ton tai")
    if kpi:
        get_kpi(session, kpi)
    s = get_source(session, source)
    lo = parse_at(period_type, from_, s) if from_ else None
    hi = parse_at(period_type, to, s) if to else None
    if lo and hi and lo > hi:
        raise HTTPException(status_code=422, detail="'from' phai nho hon hoac bang 'to'")
    view, tcol, extra = MV[period_type]
    ttype = "date" if period_type == "day" else "timestamptz"
    rows = session.execute(
        text(
            f"SELECT m.kpi_code, m.kpi_name, m.unit, m.{tcol} AS at, {POINT_COLS}{extra} "
            f"FROM {view} m "
            "WHERE m.region_code = :rc AND m.source_code = :src "
            "AND (CAST(:kpi AS text) IS NULL OR m.kpi_code = :kpi) "
            f"AND (CAST(:lo AS {ttype}) IS NULL OR m.{tcol} >= :lo) "
            f"AND (CAST(:hi AS {ttype}) IS NULL OR m.{tcol} <= :hi) "
            f"ORDER BY (SELECT display_order FROM kpis WHERE kpi_id = m.kpi_id), m.{tcol}"
        ),
        {"rc": region_code, "src": s["source_code"], "kpi": kpi, "lo": lo, "hi": hi},
    ).mappings()
    kpis: dict[str, dict] = {}
    for r in rows:
        point = to_item(r)
        meta = {key: point.pop(key) for key in ("kpi_code", "kpi_name", "unit")}
        kpis.setdefault(meta["kpi_code"], {**meta, "series": []})["series"].append(point)
    return {**region, "source": s, "period_type": period_type, "kpis": list(kpis.values())}


@router.get("/compare")
def compare(
    session: SessionDep,
    kpi: str,
    a: Annotated[str, Query(description=AtDesc)],
    b: Annotated[str, Query(description=AtDesc)],
    level: Level = "province",
    period_type: PeriodType = "day",
    region: RegionFilter = None,
    source: SourceParam = None,
) -> dict:
    """So sanh 1 KPI giua 2 moc. delta = B - A; null neu 1 trong 2 moc khong co gia tri."""
    k = get_kpi(session, kpi)
    s = get_source(session, source)
    at_a, at_b = parse_at(period_type, a, s), parse_at(period_type, b, s)
    view, tcol, _ = MV[period_type]
    rows = session.execute(
        text(
            "SELECT x.region_code, x.region_name, "
            "x.value::float8 AS value_a, x.status AS status_a, x.quality_level AS quality_level_a, "
            "y.value::float8 AS value_b, y.status AS status_b, y.quality_level AS quality_level_b "
            f"FROM {view} x JOIN {view} y ON y.region_code = x.region_code "
            "AND y.kpi_code = x.kpi_code AND y.source_code = x.source_code "
            f"AND y.{tcol} = :b WHERE x.source_code = :src AND x.kpi_code = :kpi "
            f"AND x.region_level = :lvl AND x.{tcol} = :a "
            f"AND {region_filter('x.region_code')} "
            "ORDER BY x.region_code"
        ),
        {
            "src": s["source_code"],
            "kpi": kpi,
            "lvl": level,
            "a": at_a,
            "b": at_b,
            "regions": region,
        },
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
        "level": level,
        "period_type": period_type,
        "a": at_a,
        "b": at_b,
        "items": items,
    }
