import os
from pathlib import Path

# Base directory for the KrishiMitra project
BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        """Application configuration loaded from .env."""
        DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/krishi_precision_db"
        GEMINI_API_KEY: str = ""
        CHROMA_DB_PATH: str = str(BASE_DIR / "chroma_db")

        model_config = SettingsConfigDict(
            env_file=(str(BASE_DIR / ".env"), ".env"),
            env_file_encoding="utf-8",
            extra="ignore",
        )

    settings = Settings()
except ImportError:
    try:
        import dotenv
        dotenv.load_dotenv(str(BASE_DIR / ".env"))
        dotenv.load_dotenv()
    except ImportError:
        pass

    class FallbackSettings:
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://root:password@localhost:3306/krishi_precision_db",
        )
        GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", str(BASE_DIR / "chroma_db"))

    settings = FallbackSettings()
