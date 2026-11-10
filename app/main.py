import json
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_session
from app.routes_kpi import router as kpi_router

app = FastAPI(
    title="N4.6 - Network Quality Map API (sandbox)",
    version="0.1.0",
    description="Ban thu cua Backend. Hop dong API chinh thuc: docs/api-contract.md",
)

# Cho phep frontend chay local goi API (Vite: 5173). Se siet lai khi trien khai.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(kpi_router)

SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
def health_db(session: SessionDep) -> dict:
    try:
        version = session.execute(text("SELECT postgis_lib_version()")).scalar_one()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Khong ket noi duoc CSDL") from exc
    return {"status": "ok", "postgis": version}


@app.get("/api/v1/kpis", tags=["kpi"])
def list_kpis(session: SessionDep) -> list[dict]:
    rows = session.execute(
        text(
            "SELECT code, name, unit, description, higher_is_better "
            "FROM kpi_definition ORDER BY code"
        )
    ).mappings()
    return [dict(r) for r in rows]


@app.get("/api/v1/regions", tags=["region"])
def list_regions(
    session: SessionDep,
    simplify: Annotated[float, Query(ge=0, le=0.01, description="Do don gian hoa (do)")] = 0,
) -> dict:
    """Tra ve GeoJSON FeatureCollection ranh gioi vung. Khong chua toa do tram."""
    rows = session.execute(
        text(
            "SELECT region_code, name, level, "
            "ST_AsGeoJSON(ST_Multi(ST_SimplifyPreserveTopology(geom, :tol)), 6) AS geometry "
            "FROM region ORDER BY region_code"
        ),
        {"tol": simplify},
    ).mappings()
    features = [
        {
            "type": "Feature",
            "id": r["region_code"],
            "properties": {"region_code": r["region_code"], "name": r["name"], "level": r["level"]},
            "geometry": json.loads(r["geometry"]),
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features}
