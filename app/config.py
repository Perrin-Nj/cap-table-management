# Updated app/config.py
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings using Pydantic for validation and type safety.
    Environment variables automatically loaded and validated.
    """

    # Database configuration
    database_url: str = "postgresql://cap_table_user:password@localhost/cap_table_db"

    # JWT configuration
    secret_key: str = "secret-key-for-our-tests-cap-table-v1.0"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 1 hour, We keep this long for testing purposes
    # Application configuration
    app_name: str = "Cap Table Management System"
    debug: bool = False

    # PDF generation settings
    company_name: str = "Cap Table Management Inc."
    company_logo_path: Optional[str] = None

    class Config:
        env_file = ".env"  # Not provided for testing, but aims at loading env variables from .env file


# Singleton pattern for configuration
settings = Settings()
