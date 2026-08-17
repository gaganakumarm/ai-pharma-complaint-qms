from typing import Any

from app.ai.providers import ComplaintExtractionProvider
from app.domain import SourceType
from app.schemas.extraction import ProcessTextResponse


class TextComplaintProcessingService:
    def __init__(self, graph: Any, provider: ComplaintExtractionProvider) -> None:
        self.graph = graph
        self.provider = provider

    async def process(self, text: str) -> ProcessTextResponse:
        result = await self.graph.ainvoke(
            {"raw_text": text, "source_type": SourceType.TEXT, "execution_trace": []}
        )
        return ProcessTextResponse(
            input_length=len(result["normalized_text"]),
            extracted_complaint=result["extracted_complaint"],
            warnings=result["validation_warnings"],
            assistant_message=result["assistant_message"],
            model=self.provider.model,
        )
