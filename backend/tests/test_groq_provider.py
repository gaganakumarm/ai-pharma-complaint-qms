import json
from types import SimpleNamespace

import httpx
import pytest
from groq import AuthenticationError

from app.ai.providers import GroqComplaintExtractionProvider
from app.core.exceptions import MissingAIConfigurationError, ProviderAuthenticationError
from app.schemas.correction import CorrectableComplaint
from app.schemas.extraction import ExtractedComplaint
from tests.test_text_processing import assessment, extraction


class FakeCompletions:
    def __init__(self, contents: list[str]) -> None:
        self.contents = contents
        self.calls = 0

    async def create(self, **_kwargs: object) -> object:
        content = self.contents[self.calls]
        self.calls += 1
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


class FailingCompletions:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    async def create(self, **_kwargs: object) -> object:
        self.calls += 1
        raise self.error


async def test_missing_configuration_is_controlled() -> None:
    provider = GroqComplaintExtractionProvider("", "model")
    with pytest.raises(MissingAIConfigurationError):
        await provider.extract("complaint")


async def test_malformed_output_gets_exactly_one_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completions = FakeCompletions(
        ["not-json", json.dumps(extraction(product_type="FDF"))]
    )
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr("app.ai.providers.AsyncGroq", lambda **_kwargs: fake_client)
    provider = GroqComplaintExtractionProvider("configured", "model")
    result = await provider.extract("complaint")
    assert result["product_type"].value == "FDF"
    assert completions.calls == 2


async def test_malformed_assessment_gets_exactly_one_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completions = FakeCompletions(["not-json", json.dumps(assessment())])
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr("app.ai.providers.AsyncGroq", lambda **_kwargs: fake_client)
    provider = GroqComplaintExtractionProvider("configured", "model")
    result = await provider.assess_complaint(
        ExtractedComplaint.model_validate(extraction(product_type="API"))
    )
    assert result["suggested_severity"].value == "MAJOR"
    assert completions.calls == 2


async def test_assessment_authentication_failure_does_not_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("POST", "https://api.groq.com")
    response = httpx.Response(401, request=request)
    completions = FailingCompletions(
        AuthenticationError("unauthorised", response=response, body=None)
    )
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr("app.ai.providers.AsyncGroq", lambda **_kwargs: fake_client)
    provider = GroqComplaintExtractionProvider("configured", "model")
    with pytest.raises(ProviderAuthenticationError):
        await provider.assess_complaint(ExtractedComplaint.model_validate(extraction()))
    assert completions.calls == 1


async def test_malformed_correction_gets_exactly_one_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = {
        "updates": [{"field": "batch_lot_number", "value": "BMX240602"}],
        "clarification_required": False,
        "clarification_question": None,
    }
    completions = FakeCompletions(["not-json", json.dumps(valid)])
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr("app.ai.providers.AsyncGroq", lambda **_kwargs: fake_client)
    provider = GroqComplaintExtractionProvider("configured", "model")
    current = dict.fromkeys(CorrectableComplaint.model_fields)
    result = await provider.extract_correction(
        CorrectableComplaint.model_validate(current), "Correct the batch"
    )
    assert result["updates"][0]["field"].value == "batch_lot_number"
    assert completions.calls == 2


async def test_correction_authentication_failure_does_not_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("POST", "https://api.groq.com")
    response = httpx.Response(401, request=request)
    completions = FailingCompletions(
        AuthenticationError("unauthorised", response=response, body=None)
    )
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr("app.ai.providers.AsyncGroq", lambda **_kwargs: fake_client)
    provider = GroqComplaintExtractionProvider("configured", "model")
    current = dict.fromkeys(CorrectableComplaint.model_fields)
    with pytest.raises(ProviderAuthenticationError):
        await provider.extract_correction(
            CorrectableComplaint.model_validate(current), "Change status to committed"
        )
    assert completions.calls == 1
