from typing import Any

from app.ai.providers import ComplaintExtractionProvider
from app.schemas.correction import (
    ComplaintCorrectionRequest,
    ComplaintCorrectionResponse,
)
from app.schemas.enhancements import DuplicateCheckRequest
from app.services.completeness import ComplaintCompletenessChecker
from app.services.duplicates import DuplicateDetectionService

DUPLICATE_FIELDS = {
    "product_name",
    "batch_lot_number",
    "complaint_category",
    "complaint_description",
    "affected_quantity",
    "manufacturing_date",
    "expiry_retest_date",
}


class ComplaintCorrectionService:
    def __init__(
        self,
        graph: Any,
        provider: ComplaintExtractionProvider,
        duplicate_service: DuplicateDetectionService | None = None,
    ) -> None:
        self.graph = graph
        self.provider = provider
        self.duplicate_service = duplicate_service
        self.completeness_checker = ComplaintCompletenessChecker()

    async def correct(
        self, request: ComplaintCorrectionRequest
    ) -> ComplaintCorrectionResponse:
        result = await self.graph.ainvoke(
            {
                "current_complaint": request.current_complaint,
                "instruction": request.instruction,
                "current_quality_assessment": request.current_quality_assessment,
                "current_rca_capa_recommendations": (
                    request.current_rca_capa_recommendations
                ),
                "execution_trace": [],
            }
        )
        updated = result["updated_complaint"]
        completeness = self.completeness_checker.assess(updated)
        relevant_duplicate_change = bool(
            {field.value for field in result["changed_fields"]} & DUPLICATE_FIELDS
        )
        duplicates = request.current_possible_duplicate_matches
        if relevant_duplicate_change and self.duplicate_service:
            duplicate_result = await self.duplicate_service.check(
                DuplicateCheckRequest(
                    product_name=updated.product_name,
                    batch_lot_number=updated.batch_lot_number,
                    complaint_category=updated.complaint_category,
                    complaint_description=updated.complaint_description,
                    affected_quantity=updated.affected_quantity,
                    manufacturing_date=updated.manufacturing_date,
                    expiry_retest_date=updated.expiry_retest_date,
                )
            )
            duplicates = duplicate_result.matches
        return ComplaintCorrectionResponse(
            patch=result["patch"],
            updated_complaint=updated,
            changed_fields=result["changed_fields"],
            warnings=result["warnings"],
            quality_assessment=result["quality_assessment"],
            completeness_assessment=completeness,
            possible_duplicate_matches=duplicates,
            rca_capa_recommendations=result["rca_capa_recommendations"],
            assistant_message=result["assistant_message"],
            status=result["status"],
            model=self.provider.model,
        )
