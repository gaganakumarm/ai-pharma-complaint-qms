from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import system_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.infrastructure.database import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.database = Database(app_settings.database_url)
        yield
        await application.state.database.dispose()

    application = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in app_settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(system_router)
    register_error_handlers(application)
    return application


app = create_app()
