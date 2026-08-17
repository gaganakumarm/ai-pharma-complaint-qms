from collections.abc import Mapping
from typing import Any

import app.main as main_module
from app.core.config import Settings
from app.domain import ProductType
from app.schemas.correction import CorrectableComplaint
from app.schemas.extraction import ExtractedComplaint


class DeterministicAcceptanceProvider:
    model = "deterministic-fake-groq"

    async def extract(self, text: str) -> Mapping[str, Any]:
        is_api = "Metformin" in text or "MET-API" in text
        incomplete = "No batch or quantity" in text
        values = dict.fromkeys(ExtractedComplaint.model_fields)
        if incomplete:
            values.update(
                product_type=ProductType.UNKNOWN,
                complaint_description="A customer reports damaged tablets.",
            )
        elif is_api:
            values.update(
                complaint_source="Fictional API PDF",
                customer_name="Fictional API Customer",
                product_type=ProductType.API,
                product_name="Metformin Hydrochloride API",
                product_strength_grade="IP/BP",
                batch_lot_number="MET-API-77A",
                affected_quantity="25 kg in one HDPE drum",
                expiry_retest_date="January 2028",
                complaint_description="Fictional API material complaint.",
            )
        else:
            values.update(
                complaint_source="Fictional FDF PDF",
                customer_name="Fictional FDF Customer",
                product_type=ProductType.FDF,
                product_name="Amoxicillin Capsules",
                product_strength_grade="500 mg",
                batch_lot_number="AMX-FDF-2407",
                affected_quantity="12 capsules",
                complaint_description="Fictional dented carton complaint.",
            )
        return ExtractedComplaint.model_validate(values).model_dump()

    async def assess_complaint(
        self, complaint: ExtractedComplaint | CorrectableComplaint
    ) -> Mapping[str, Any]:
        incomplete = complaint.batch_lot_number is None
        description = complaint.complaint_description or "Reported fictional issue."
        return {
            "complaint_category": complaint.complaint_category
            if isinstance(complaint, CorrectableComplaint)
            and complaint.complaint_category
            else "Product quality defect",
            "structured_complaint_description": description,
            "suggested_severity": "MAJOR",
            "severity_rationale": "Deterministic fictional assessment for QA review.",
            "initial_risk_assessment": "Potential quality impact requires QA review.",
            "suggested_next_action": "QA should review the fictional complaint.",
            "assessment_status": "NEEDS_INFORMATION" if incomplete else "COMPLETE",
            "information_gaps": ["Batch number"] if incomplete else [],
            "human_review_required": True,
        }

    async def extract_correction(
        self, current: CorrectableComplaint, instruction: str
    ) -> Mapping[str, Any]:
        lowered = instruction.lower()
        if "number is wrong" in lowered:
            return {
                "updates": [],
                "clarification_required": True,
                "clarification_question": "Which number should change?",
            }
        if "status" in lowered or "complaint id" in lowered:
            return {
                "updates": [],
                "clarification_required": True,
                "clarification_question": (
                    "Protected fields cannot be changed. Which complaint-source field "
                    "should change?"
                ),
            }
        if "remove" in lowered and "expiry" in lowered:
            updates = [{"field": "expiry_retest_date", "value": None}]
        elif "chg-260712a" in lowered:
            updates = [
                {"field": "batch_lot_number", "value": "CHG-260712A"},
                {"field": "affected_quantity", "value": "50 kg in 2 HDPE drums"},
            ]
        elif "bmx240602" in lowered:
            updates = [
                {"field": "batch_lot_number", "value": "BMX240602"},
                {"field": "affected_quantity", "value": "48 capsules"},
            ]
        elif "fictional retry" in lowered:
            updates = [{"field": "customer_name", "value": "Fictional Retry Company"}]
        else:
            updates = [{"field": "customer_name", "value": current.customer_name}]
        return {
            "updates": updates,
            "clarification_required": False,
            "clarification_question": None,
        }


settings = Settings(database_url="sqlite+aiosqlite:///:memory:")
main_module.GroqComplaintExtractionProvider = (  # type: ignore[misc]
    lambda *_args, **_kwargs: DeterministicAcceptanceProvider()
)
app = main_module.create_app(settings)
