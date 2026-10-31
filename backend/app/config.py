"""Configuration settings for OmniContext."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OmniContext"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    
    # Offline mock mode for zero-credential test and demo resilience
    offline_mock_mode: bool = Field(default=True, validation_alias="OFFLINE_MOCK_MODE")
    
    # Seed data path
    seed_data_path: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "seed",
        "enterprise_knowledge.json"
    )

settings = Settings()
