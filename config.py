import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./license_db.db"
    SECRET_KEY: str = "your-very-secure-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "uploads"
    ALLOWED_IPS: list[str] = ["127.0.0.1", "192.168.0.159", "192.168.0.17"]


    class Config:
        env_file = ".env"

settings = Settings()

# Ensure upload directory exists
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
