from typing import Any

from app.ai.providers import ComplaintExtractionProvider
from app.schemas.correction import (
    ComplaintCorrectionRequest,
    ComplaintCorrectionResponse,
)


class ComplaintCorrectionService:
    def __init__(self, graph: Any, provider: ComplaintExtractionProvider) -> None:
        self.graph = graph
        self.provider = provider

    async def correct(
        self, request: ComplaintCorrectionRequest
    ) -> ComplaintCorrectionResponse:
        result = await self.graph.ainvoke(
            {
                "current_complaint": request.current_complaint,
                "instruction": request.instruction,
                "current_quality_assessment": request.current_quality_assessment,
                "execution_trace": [],
            }
        )
        return ComplaintCorrectionResponse(
            patch=result["patch"],
            updated_complaint=result["updated_complaint"],
            changed_fields=result["changed_fields"],
            warnings=result["warnings"],
            quality_assessment=result["quality_assessment"],
            assistant_message=result["assistant_message"],
            status=result["status"],
            model=self.provider.model,
        )
