import aiohttp
from contextlib import asynccontextmanager
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers.auths import router as auth_router
from app.routers.users import router as user_router
from app.routers.chat_sessions import router as chat_sessions_router
from app.routers.artifacts import router as artifacts_router
from app.core.settings import get_settings
from app.middlewares import cors_middleware
from app.utils.mongodb import get_mongodb_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        # Initialize aiohttp session
        aiohttp_session = aiohttp.ClientSession()

        # Initialize MongoDB client
        app.mongodb_client = get_mongodb_client()
        app.db = app.mongodb_client[settings.MONGO_DATABASE_NAME]

        yield

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup
        try:
            app.mongodb_client.close()
            await aiohttp_session.close()
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
app.include_router(chat_sessions_router, prefix="/chat", tags=["Chat Sessions"])
app.include_router(artifacts_router, prefix="/chat", tags=["Artifacts"])

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Template"}

@app.get("/chat-ui")
async def chat_ui():
    return FileResponse("app/static/chat_sessions.html")