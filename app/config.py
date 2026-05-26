from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/catalog_db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Messenger Bot
    MESSENGER_VERIFY_TOKEN: str = "shelfy_verify_2024"
    MESSENGER_PAGE_TOKEN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
