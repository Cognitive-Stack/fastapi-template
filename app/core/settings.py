from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Security Settings (JWT)
    SECRET_KEY: str = "secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # MongoDB Settings
    MONGO_DATABASE_NAME: str = "database"
    MONGO_USERNAME: str = "admin"
    MONGO_PASSWORD: str = ""
    MONGO_HOST: str = "localhost"
    MONGO_PORT: str = "27017"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def MONGODB_URI(self) -> str:
        if not self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}"

        escaped_username = quote_plus(self.MONGO_USERNAME)
        escaped_password = quote_plus(self.MONGO_PASSWORD)
        return f"mongodb://{escaped_username}:{escaped_password}@{self.MONGO_HOST}:{self.MONGO_PORT}"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()
