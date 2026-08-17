from collections.abc import Mapping
from typing import Any

from app.domain import ProductType
from app.schemas.enhancements import CompletenessAssessment, CompletenessStatus

REQUIRED_FIELDS = {
    "customer_name": "Customer name",
    "product_name": "Product name",
    "batch_lot_number": "Batch/Lot number",
    "complaint_category": "Complaint category",
    "complaint_description": "Complaint description",
}
COMMON_RECOMMENDED_FIELDS = {
    "complaint_source": "Complaint source",
    "affected_quantity": "Affected quantity",
    "manufacturing_date": "Manufacturing date",
    "expiry_retest_date": "Expiry/Retest date",
    "originating_site_block": "Manufacturing site",
    "impacted_non_product_materials": "Material type/context",
}
PLACEHOLDERS = {
    "n/a",
    "na",
    "none",
    "not applicable",
    "not available",
    "not provided",
    "unknown",
    "unavailable",
}


def is_meaningful(value: object) -> bool:
    if value is None:
        return False
    normalized = str(value).strip().casefold().rstrip(".")
    return bool(normalized) and normalized not in PLACEHOLDERS


class ComplaintCompletenessChecker:
    def assess(self, complaint: Any) -> CompletenessAssessment:
        values: Mapping[str, object] = (
            complaint if isinstance(complaint, Mapping) else complaint.model_dump()
        )
        missing_required = [
            field for field in REQUIRED_FIELDS if not is_meaningful(values.get(field))
        ]
        recommended = dict(COMMON_RECOMMENDED_FIELDS)
        product_type = values.get("product_type")
        if product_type in (ProductType.FDF, ProductType.API, "FDF", "API"):
            recommended["product_strength_grade"] = (
                "Product strength"
                if str(product_type) == "FDF"
                else "API grade/specification"
            )
        missing_recommended = [
            field for field in recommended if not is_meaningful(values.get(field))
        ]
        present = len(REQUIRED_FIELDS) - len(missing_required)
        percentage = present * 100 // len(REQUIRED_FIELDS)
        if missing_required:
            labels = ", ".join(REQUIRED_FIELDS[field] for field in missing_required)
            guidance = f"Provide the missing required information: {labels}."
            status = CompletenessStatus.NEEDS_INFORMATION
        else:
            guidance = (
                "All required commit fields are present. Review recommended gaps and "
                "the full draft before manual commit."
            )
            status = CompletenessStatus.COMPLETE
        return CompletenessAssessment(
            status=status,
            required_fields_present=present,
            total_required_fields=len(REQUIRED_FIELDS),
            completeness_percentage=percentage,
            missing_required_fields=missing_required,
            missing_recommended_fields=missing_recommended,
            guidance=guidance,
        )
