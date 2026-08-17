import json
from types import SimpleNamespace

import pytest

from app.ai.providers import GroqComplaintExtractionProvider
from app.core.exceptions import MissingAIConfigurationError
from tests.test_text_processing import extraction


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
