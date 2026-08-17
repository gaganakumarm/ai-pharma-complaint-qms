import asyncio
import os

from app.ai.providers import GroqComplaintExtractionProvider
from app.core.config import Settings
from app.core.exceptions import ProviderRateLimitError
from app.schemas.assessment import ComplaintQualityAssessment
from app.schemas.enhancements import RcaCapaRecommendations
from app.schemas.extraction import ExtractedComplaint


async def main() -> None:
    settings = Settings()
    provider = GroqComplaintExtractionProvider(
        os.environ.get("GROQ_API_KEY", ""), settings.groq_model
    )
    assessment = ComplaintQualityAssessment(
        complaint_category="Fictional appearance complaint",
        structured_complaint_description=(
            "Fictional product discoloration was reported."
        ),
        suggested_severity="MAJOR",
        severity_rationale="Potential quality impact requires investigation.",
        initial_risk_assessment="Evidence is incomplete and requires QA review.",
        suggested_next_action=("Authorised QA should review the fictional evidence."),
        assessment_status="COMPLETE",
        information_gaps=[],
    )
    for product_type in ("FDF", "API"):
        complaint = ExtractedComplaint(
            complaint_source="Fictional smoke test",
            customer_name="Fictional Customer",
            product_type=product_type,
            product_name="Fictional Product",
            product_strength_grade="500 mg" if product_type == "FDF" else "USP",
            batch_lot_number="FAKE-LOT-1",
            affected_quantity="1 unit",
            manufacturing_date=None,
            expiry_retest_date=None,
            originating_site_block=None,
            impacted_non_product_materials=None,
            complaint_description="Fictional appearance complaint.",
        )
        try:
            payload = await provider.recommend_rca_capa(complaint, assessment)
        except ProviderRateLimitError:
            print(f"{product_type}_RCA_CAPA=RATE_LIMITED")
            return
        validated = RcaCapaRecommendations.model_validate(payload)
        print(
            f"{product_type}_RCA_CAPA=VALID;"
            f"HUMAN_REVIEW={validated.human_review_required}"
        )


if __name__ == "__main__":
    asyncio.run(main())
