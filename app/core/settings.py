from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Azure Settings
    AZURE_ENDPOINT: str
    AZURE_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_VERSION: str

    # MongoDB Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "database"
    MONGO_USERNAME: str = "admin"
    MONGO_PASSWORD: str = ""
    MONGO_HOST: str = "localhost"
    MONGO_PORT: str = "27017"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # RabbitMQ Settings
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USERNAME: str = "admin"
    RABBITMQ_PASSWORD: str = ""
    RABBITMQ_VHOST: str = "/"

    @property
    def RABBITMQ_URL(self) -> str:
        if not self.RABBITMQ_PASSWORD:
            return f"amqp://{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        return f"amqp://{self.RABBITMQ_USERNAME}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"

    @property
    def MONGODB_URL(self) -> str:
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
