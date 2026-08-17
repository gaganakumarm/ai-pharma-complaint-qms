from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.correction_graph import build_correction_graph
from app.ai.graph import build_complaint_graph
from app.ai.providers import GroqComplaintExtractionProvider
from app.api.routes import complaints_router, system_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.infrastructure.database import Database
from app.services.correction_processing import ComplaintCorrectionService
from app.services.documents import DocumentComplaintProcessingService, PdfTextExtractor
from app.services.text_processing import TextComplaintProcessingService


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.database = Database(app_settings.database_url)
        provider = GroqComplaintExtractionProvider(
            app_settings.groq_api_key, app_settings.groq_model
        )
        graph = build_complaint_graph(provider, app_settings.max_text_input_length)
        text_service = TextComplaintProcessingService(graph, provider)
        application.state.text_processing_service = text_service
        correction_graph = build_correction_graph(
            provider, app_settings.max_correction_instruction_length
        )
        application.state.correction_service = ComplaintCorrectionService(
            correction_graph, provider
        )
        application.state.document_processing_service = (
            DocumentComplaintProcessingService(
                text_service=text_service,
                extractor=PdfTextExtractor(),
                maximum_upload_bytes=app_settings.max_upload_size_mb * 1024 * 1024,
                maximum_upload_mb=app_settings.max_upload_size_mb,
                maximum_pages=app_settings.max_pdf_pages,
                maximum_text_length=app_settings.max_pdf_text_length,
            )
        )
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
    application.include_router(complaints_router)
    register_error_handlers(application)
    return application


app = create_app()
