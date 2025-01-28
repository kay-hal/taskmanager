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
    env_file = ".env.production" if env == "production" else ".env"
    return Settings(_env_file=env_file) 