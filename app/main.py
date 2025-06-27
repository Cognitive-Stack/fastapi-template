import subprocess
import aiohttp
from contextlib import asynccontextmanager
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auths import router as auth_router
from app.routers.users import router as user_router
from app.core.settings import get_settings
from app.middlewares import cors_middleware
from app.utils.mongodb import get_mongodb_client
from app.utils.rabbitmq import get_rabbitmq_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        # Initialize aiohttp session
        aiohttp_session = aiohttp.ClientSession()

        # Initialize MongoDB client
        app.mongodb_client = get_mongodb_client()
        app.db = app.mongodb_client[settings.DATABASE_NAME]

        # Initialize RabbitMQ connection
        app.rabbitmq_connection = await get_rabbitmq_connection()
        # Start the consumer process
        subprocess.Popen(["python", "-m", "app.workers.consumer"])

        yield

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup
        try:
            app.mongodb_client.close()
            await aiohttp_session.close()
            await app.rabbitmq_connection.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


# Create the FastAPI app
app = FastAPI(
    title="FastAPI Template",
    description="API for FastAPI Template",
    version="0.1.0",
    lifespan=lifespan,
)

cors_middleware.add(app)

app.include_router(auth_router, prefix="/auths", tags=["Auths"])
app.include_router(user_router, prefix="/users", tags=["Users"])

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Template"}