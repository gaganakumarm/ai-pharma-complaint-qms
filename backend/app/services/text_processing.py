from typing import Any

from app.ai.providers import ComplaintExtractionProvider
from app.domain import SourceType
from app.schemas.enhancements import DuplicateCheckRequest
from app.schemas.extraction import ProcessTextResponse
from app.services.duplicates import DuplicateDetectionService


class TextComplaintProcessingService:
    def __init__(
        self,
        graph: Any,
        provider: ComplaintExtractionProvider,
        duplicate_service: DuplicateDetectionService | None = None,
    ) -> None:
        self.graph = graph
        self.provider = provider
        self.duplicate_service = duplicate_service

    async def process(
        self, text: str, source_type: SourceType = SourceType.TEXT
    ) -> ProcessTextResponse:
        result = await self.graph.ainvoke(
            {"raw_text": text, "source_type": source_type, "execution_trace": []}
        )
        extracted = result["extracted_complaint"]
        assessment = result["quality_assessment"]
        duplicates = []
        if self.duplicate_service:
            duplicate_result = await self.duplicate_service.check(
                DuplicateCheckRequest(
                    product_name=extracted.product_name,
                    batch_lot_number=extracted.batch_lot_number,
                    complaint_category=assessment.complaint_category,
                    complaint_description=assessment.structured_complaint_description,
                    affected_quantity=extracted.affected_quantity,
                    manufacturing_date=extracted.manufacturing_date,
                    expiry_retest_date=extracted.expiry_retest_date,
                )
            )
            duplicates = duplicate_result.matches
        return ProcessTextResponse(
            source_type=source_type,
            input_length=len(result["normalized_text"]),
            extracted_complaint=extracted,
            quality_assessment=assessment,
            completeness_assessment=result["completeness_assessment"],
            possible_duplicate_matches=duplicates,
            rca_capa_recommendations=result["rca_capa_recommendations"],
            warnings=result["validation_warnings"],
            assistant_message=result["assistant_message"],
            model=self.provider.model,
        )
