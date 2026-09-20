from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "CATÁLOGO API"
    database_url: str = "sqlite:///./catalogo.db"
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    uploads_dir: Path = Path("uploads")
    auth0_domain: str = ""
    auth0_audience: str = ""
    auth0_algorithms: Annotated[list[str], NoDecode] = ["RS256"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("auth0_algorithms", mode="before")
    @classmethod
    def parse_auth0_algorithms(cls, value: object) -> object:
        if isinstance(value, str):
            return [
                algorithm.strip() for algorithm in value.split(",") if algorithm.strip()
            ]
        return value

    @property
    def auth0_issuer(self) -> str:
        return f"https://{self.auth0_domain.strip('/')}/"

    @property
    def product_upload_dir(self) -> Path:
        return self.uploads_dir / "products"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
