from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# Bang cua du an nam trong schema PostgreSQL n46; PostGIS o public.
# Mui gio phien = gio VN de API tra thoi gian dang +07:00 thay vi UTC.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"options": "-c search_path=n46,public -c timezone=Asia/Ho_Chi_Minh"},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
