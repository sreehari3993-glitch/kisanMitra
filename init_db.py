import sys
from pathlib import Path

# Ensure project root is in sys.path so backend module can be imported cleanly
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import Base, engine
import backend.models  # Required so all models register with Base.metadata


def init_db() -> None:
    """Creates all defined database tables in MySQL using SQLAlchemy 2.0 create_all."""
    print("Connecting to MySQL and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_db()
