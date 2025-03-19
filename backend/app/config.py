from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./tasks.db"
    anthropic_api_key: str
    admin_token: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings():
    env = os.getenv("ENVIRONMENT", "development")
    # Check if running on Render
    is_render = os.environ.get('RENDER', False)
    
    if is_render:
        env = "production"
        # Log that we're using Render environment
        import logging
        logging.getLogger(__name__).info("Running in Render production environment")
    
    env_file = ".env.production" if env == "production" else ".env"
    settings = Settings(_env_file=env_file)
    
    # Override database_url if set in environment
    if db_url := os.environ.get("DATABASE_URL"):
        settings.database_url = db_url
    
    return settings