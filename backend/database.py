from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

try:
    from backend.config import settings
except ImportError:
    from .config import settings

# SQLAlchemy 2.0 Engine with tuned connection pooling for MySQL
engine = create_engine(
    settings.DATABASE_URL,
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
