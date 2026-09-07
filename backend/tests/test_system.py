from httpx import AsyncClient

from app.ai.providers import GroqComplaintExtractionProvider
from app.core.config import Settings
from app.main import create_app
from tests.fake_acceptance_server import DeterministicAcceptanceProvider


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_verifies_database(client: AsyncClient) -> None:
    response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_provider_factory_is_lazy_and_shared_by_processing_services() -> None:
    provider = DeterministicAcceptanceProvider()
    calls = 0

    def factory() -> DeterministicAcceptanceProvider:
        nonlocal calls
        calls += 1
        return provider

    app = create_app(
        Settings(database_url="sqlite+aiosqlite:///:memory:"), provider_factory=factory
    )
    assert calls == 0
    async with app.router.lifespan_context(app):
        assert calls == 1
        assert app.state.text_processing_service.provider is provider
        assert app.state.correction_service.provider is provider
        response = await app.state.text_processing_service.process("Dented carton")
        assert response.model == provider.model
        assert response.extracted_complaint.batch_lot_number == "AMX-FDF-2407"


async def test_default_provider_uses_configured_groq_model() -> None:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        groq_api_key="test-configured-key",
        groq_model="test-configured-model",
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        provider = app.state.text_processing_service.provider
        assert isinstance(provider, GroqComplaintExtractionProvider)
        assert provider.api_key == settings.groq_api_key
        assert provider.model == settings.groq_model
        assert app.state.correction_service.provider is provider
