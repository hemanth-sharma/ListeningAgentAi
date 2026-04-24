import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str 
    SECRET_KEY: str = "dev"
    SCRAPER_URL: str = "http://localhost:8081/scrape"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()