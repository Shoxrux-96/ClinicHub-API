from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    APP_NAME: str = "Clinic SaaS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # First Owner
    FIRST_OWNER_EMAIL: str
    FIRST_OWNER_PASSWORD: str
    FIRST_OWNER_NAME: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()