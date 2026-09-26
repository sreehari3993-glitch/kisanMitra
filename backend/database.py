from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

try:
    from backend.config import settings
except ImportError:
    from .config import settings

# Format connection URL for SQLAlchemy compatibility (Railway mysql:// to mysql+pymysql://)
def _build_engine():
    raw_url = str(getattr(settings, "DATABASE_URL", "") or "").strip().strip("\"'").strip()

    # If empty or missing scheme, fallback gracefully to SQLite so container never crashes
    if not raw_url or "://" not in raw_url:
        print(f"[Database Notice] DATABASE_URL '{raw_url}' is not a valid URL. Using local SQLite database.")
        return create_engine("sqlite:///./krishi_precision_db.sqlite3", connect_args={"check_same_thread": False})

    # Adapt Railway/Heroku/Render standard database URLs for SQLAlchemy
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+"):
        raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif raw_url.startswith("mysql://") and not raw_url.startswith("mysql+"):
        raw_url = raw_url.replace("mysql://", "mysql+pymysql://", 1)

    try:
        if "sqlite" in raw_url:
            return create_engine(raw_url, connect_args={"check_same_thread": False})
        return create_engine(
            raw_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
    except Exception as exc:
        print(f"[Database Error] Could not initialize engine with '{raw_url}': {exc}. Falling back to SQLite.")
        return create_engine("sqlite:///./krishi_precision_db.sqlite3", connect_args={"check_same_thread": False})


engine = _build_engine()

# Session factory for DB interactions
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# SQLAlchemy 2.0 DeclarativeBase
class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session and safely closing it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
