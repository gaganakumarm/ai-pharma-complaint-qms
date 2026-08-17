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

from app.ai.prompts import (
    ASSESSMENT_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    assessment_user_prompt,
    user_prompt,
)
from app.core.exceptions import (
    MalformedProviderResponseError,
    MissingAIConfigurationError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.schemas.assessment import ComplaintQualityAssessment
from app.schemas.extraction import ExtractedComplaint


class ComplaintExtractionProvider(Protocol):
    model: str

    async def extract(self, text: str) -> Mapping[str, Any]: ...

    async def assess_complaint(
        self, complaint: ExtractedComplaint
    ) -> Mapping[str, Any]: ...


class GroqComplaintExtractionProvider:
    def __init__(self, api_key: str, model: str, timeout_seconds: float = 20.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def extract(self, text: str) -> Mapping[str, Any]:
        schema = ExtractedComplaint.model_json_schema()
        schema["properties"]["product_type"] = {
            "type": ["string", "null"],
            "enum": ["API", "FDF", "UNKNOWN", None],
        }
        return await self._structured_output(
            SYSTEM_PROMPT,
            user_prompt(text),
            schema,
            "pharmaceutical_complaint_extraction",
            ExtractedComplaint,
        )

    async def assess_complaint(
        self, complaint: ExtractedComplaint
    ) -> Mapping[str, Any]:
        schema = ComplaintQualityAssessment.model_json_schema()
        schema["required"] = list(schema["properties"])
        return await self._structured_output(
            ASSESSMENT_SYSTEM_PROMPT,
            assessment_user_prompt(complaint.model_dump_json()),
            schema,
            "pharmaceutical_complaint_quality_assessment",
            ComplaintQualityAssessment,
        )

    async def _structured_output(
        self,
        system_prompt: str,
        prompt: str,
        schema: dict[str, Any],
        schema_name: str,
        response_model: type[ExtractedComplaint] | type[ComplaintQualityAssessment],
    ) -> Mapping[str, Any]:
        if not self.api_key.strip():
            raise MissingAIConfigurationError
        for attempt in range(2):
            client: Any | None = None
            try:
                client = AsyncGroq(api_key=self.api_key, timeout=self.timeout_seconds)
                response = await client.chat.completions.create(
                    model=self.model,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "strict": True,
                            "schema": schema,
                        },
                    },
                )
                content = response.choices[0].message.content
                parsed = json.loads(content or "{}")
                return response_model.model_validate(parsed).model_dump()
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
            finally:
                close = getattr(client, "close", None)
                if close is not None:
                    await close()
        raise MalformedProviderResponseError
