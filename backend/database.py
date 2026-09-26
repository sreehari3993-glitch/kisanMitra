from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

try:
    from backend.config import settings
except ImportError:
    from .config import settings

# Format connection URL for SQLAlchemy compatibility (Railway mysql:// to mysql+pymysql://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
elif db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

if "sqlite" in db_url:
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        db_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

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
