import os
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from urllib.parse import quote_plus
from app.core.settings import get_settings


def get_mongodb_client():
    settings = get_settings()
    mongo_uri = settings.MONGODB_URI

    return AsyncIOMotorClient(mongo_uri)
