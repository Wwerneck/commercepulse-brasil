import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Central application settings loaded from environment variables."""

    app_env: str
    log_level: str
    data_dir: Path
    bcb_base_url: str
    ibge_sidra_base_url: str
    request_timeout_seconds: int
    request_retries: int
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    mlflow_tracking_uri: str

    @property
    def bronze_dir(self) -> Path:
        return self.data_dir / "bronze"

    @property
    def silver_dir(self) -> Path:
        return self.data_dir / "silver"

    @property
    def gold_dir(self) -> Path:
        return self.data_dir / "gold"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        bcb_base_url=os.getenv("BCB_BASE_URL", "https://api.bcb.gov.br/dados/serie"),
        ibge_sidra_base_url=os.getenv("IBGE_SIDRA_BASE_URL", "https://apisidra.ibge.gov.br/values"),
        request_timeout_seconds=max(int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")), 1),
        request_retries=max(int(os.getenv("REQUEST_RETRIES", "3")), 0),
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_db=os.getenv("POSTGRES_DB", "commercepulse"),
        postgres_user=os.getenv("POSTGRES_USER", "commercepulse"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "commercepulse"),
        mlflow_tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"),
    )
