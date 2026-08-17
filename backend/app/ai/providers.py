import json
from collections.abc import Mapping
from typing import Any, Protocol

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    AuthenticationError,
    RateLimitError,
)
from pydantic import ValidationError

from app.ai.prompts import SYSTEM_PROMPT, user_prompt
from app.core.exceptions import (
    MalformedProviderResponseError,
    MissingAIConfigurationError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.schemas.extraction import ExtractedComplaint


class ComplaintExtractionProvider(Protocol):
    model: str

    async def extract(self, text: str) -> Mapping[str, Any]: ...


class GroqComplaintExtractionProvider:
    def __init__(self, api_key: str, model: str, timeout_seconds: float = 20.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def extract(self, text: str) -> Mapping[str, Any]:
        if not self.api_key.strip():
            raise MissingAIConfigurationError
        schema = ExtractedComplaint.model_json_schema()
        schema["properties"]["product_type"] = {
            "type": ["string", "null"],
            "enum": ["API", "FDF", "UNKNOWN", None],
        }
        for attempt in range(2):
            try:
                client = AsyncGroq(api_key=self.api_key, timeout=self.timeout_seconds)
                response = await client.chat.completions.create(
                    model=self.model,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt(text)},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "pharmaceutical_complaint_extraction",
                            "strict": True,
                            "schema": schema,
                        },
                    },
                )
                content = response.choices[0].message.content
                parsed = json.loads(content or "{}")
                return ExtractedComplaint.model_validate(parsed).model_dump()
            except (json.JSONDecodeError, ValidationError, IndexError, AttributeError):
                if attempt == 1:
                    raise MalformedProviderResponseError from None
            except AuthenticationError as exc:
                raise ProviderAuthenticationError from exc
            except APITimeoutError as exc:
                raise ProviderTimeoutError from exc
            except RateLimitError as exc:
                raise ProviderRateLimitError from exc
            except (APIConnectionError, APIStatusError) as exc:
                raise ProviderUnavailableError from exc
        raise MalformedProviderResponseError
