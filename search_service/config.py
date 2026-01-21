"""
Configuration management using pydantic-settings.
Loads from .env file and provides type-safe access to all settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Google Drive OAuth Configuration
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    google_drive_folder_id: str
    
    # Elasticsearch Configuration
    elasticsearch_host: str = "http://localhost:9200"
    elasticsearch_index: str = "documents"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # OAuth Token Storage
    token_file: str = "token.json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Singleton instance - import this in other modules
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection helper for FastAPI"""
    return settings
