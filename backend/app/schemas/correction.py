from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain import ProductType
from app.schemas.assessment import ComplaintQualityAssessment


class CorrectionField(StrEnum):
    COMPLAINT_SOURCE = "complaint_source"
    CUSTOMER_NAME = "customer_name"
    PRODUCT_TYPE = "product_type"
    PRODUCT_NAME = "product_name"
    PRODUCT_STRENGTH_GRADE = "product_strength_grade"
    BATCH_LOT_NUMBER = "batch_lot_number"
    AFFECTED_QUANTITY = "affected_quantity"
    MANUFACTURING_DATE = "manufacturing_date"
    EXPIRY_RETEST_DATE = "expiry_retest_date"
    ORIGINATING_SITE_BLOCK = "originating_site_block"
    IMPACTED_NON_PRODUCT_MATERIALS = "impacted_non_product_materials"
    COMPLAINT_CATEGORY = "complaint_category"
    COMPLAINT_DESCRIPTION = "complaint_description"


CorrectionValue = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)
]


class CorrectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: CorrectionField
    value: CorrectionValue | None


class ComplaintCorrectionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    updates: list[CorrectionUpdate] = Field(max_length=len(CorrectionField))
    clarification_required: bool
    clarification_question: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
        ]
        | None
    )

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        fields = [update.field for update in self.updates]
        if len(fields) != len(set(fields)):
            raise ValueError("Correction fields must not be duplicated")
        if self.clarification_required:
            if self.updates or self.clarification_question is None:
                raise ValueError("Clarification requires no updates and a question")
        elif not self.updates or self.clarification_question is not None:
            raise ValueError(
                "A correction requires updates and no clarification question"
            )
        return self


class CorrectableComplaint(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    complaint_source: str | None = Field(max_length=255)
    customer_name: str | None = Field(max_length=200)
    product_type: ProductType | None
    product_name: str | None = Field(max_length=200)
    product_strength_grade: str | None = Field(max_length=100)
    batch_lot_number: str | None = Field(max_length=100)
    affected_quantity: str | None = Field(max_length=100)
    manufacturing_date: str | None = Field(max_length=100)
    expiry_retest_date: str | None = Field(max_length=100)
    originating_site_block: str | None = Field(max_length=200)
    impacted_non_product_materials: str | None = Field(max_length=2000)
    complaint_category: str | None = Field(max_length=150)
    complaint_description: str | None = Field(max_length=5000)


class CorrectionStatus(StrEnum):
    APPLIED = "APPLIED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    NO_CHANGES = "NO_CHANGES"


class ComplaintCorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_complaint: CorrectableComplaint
    instruction: str
    current_quality_assessment: ComplaintQualityAssessment
    client_draft_revision: int | None = Field(default=None, ge=0)


class ComplaintCorrectionResponse(BaseModel):
    patch: ComplaintCorrectionPatch
    updated_complaint: CorrectableComplaint
    changed_fields: list[CorrectionField]
    warnings: list[str]
    quality_assessment: ComplaintQualityAssessment
    assistant_message: str
    status: CorrectionStatus
    model: str
