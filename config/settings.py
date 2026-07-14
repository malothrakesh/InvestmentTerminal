from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    All application settings should be accessed through
    the singleton 'settings' object.

    Values are automatically loaded from the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    APP_NAME: str = "Institutional Investing Terminal"

    APP_ENV: str = "development"

    DEBUG: bool = True

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    DATABASE_TYPE: str = "sqlite"

    DATABASE_NAME: str = "market.db"

    DATABASE_URL: str = ""

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL: str = "INFO"

    LOG_ROTATION: str = "10 MB"

    LOG_RETENTION: str = "10 days"

    # ------------------------------------------------------------------
    # Market Data
    # ------------------------------------------------------------------

    MARKET_DATA_PROVIDER: str = "yahoo"

    MARKET_DATA_TIMEOUT: int = 30

    MARKET_DATA_RETRY_COUNT: int = 3

    MARKET_DATA_BATCH_SIZE: int = 100

    MARKET_DATA_CACHE_ENABLED: bool = False

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    @property
    def LOG_DIR(self) -> Path:
        return self.BASE_DIR / "logs"

    @property
    def EXPORT_DIR(self) -> Path:
        return self.BASE_DIR / "exports"

    @property
    def DATA_DIR(self) -> Path:
        return self.BASE_DIR / "data"

    @property
    def SQLITE_DATABASE_PATH(self) -> Path:
        return self.BASE_DIR / self.DATABASE_NAME

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """
        Returns the database connection URL.

        If DATABASE_URL is supplied (e.g. PostgreSQL),
        it takes precedence.

        Otherwise SQLite is used.
        """

        if self.DATABASE_URL:
            return self.DATABASE_URL

        return f"sqlite:///{self.SQLITE_DATABASE_PATH}"

    def create_directories(self) -> None:
        """
        Create required application directories.
        """

        self.LOG_DIR.mkdir(exist_ok=True)

        self.EXPORT_DIR.mkdir(exist_ok=True)

        self.DATA_DIR.mkdir(exist_ok=True)


settings = Settings()

settings.create_directories()