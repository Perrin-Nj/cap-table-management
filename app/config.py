# Updated app/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings using Pydantic for validation and type safety.
    Environment variables automatically loaded and validated.
    """

    # Database configuration
    database_url: str = "postgresql://cap_table_user:password@localhost/cap_table_db"

    # JWT configuration
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application configuration
    app_name: str = "Cap Table Management System"
    debug: bool = False

    # PDF generation settings
    company_name: str = "Your Company Name"
    company_logo_path: Optional[str] = None

    class Config:
        env_file = ".env"


# Singleton pattern for configuration
settings = Settings()