import re
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain import ComplaintStatus

GuidanceText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


class CompletenessStatus(StrEnum):
    COMPLETE = "COMPLETE"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"


class CompletenessAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: CompletenessStatus
    required_fields_present: int = Field(ge=0)
    total_required_fields: int = Field(gt=0)
    completeness_percentage: int = Field(ge=0, le=100)
    missing_required_fields: list[str]
    missing_recommended_fields: list[str]
    guidance: GuidanceText


class DuplicateCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    current_complaint_id: uuid.UUID | None = None
    product_name: str | None = Field(default=None, max_length=200)
    batch_lot_number: str | None = Field(default=None, max_length=100)
    complaint_category: str | None = Field(default=None, max_length=150)
    complaint_description: str | None = Field(default=None, max_length=5000)
    affected_quantity: str | None = Field(default=None, max_length=100)
    manufacturing_date: str | None = Field(default=None, max_length=100)
    expiry_retest_date: str | None = Field(default=None, max_length=100)


class DuplicateMatchLevel(StrEnum):
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    STRONG_MATCH = "STRONG_MATCH"


class DuplicateMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    complaint_id: uuid.UUID
    complaint_number: str
    product_name: str
    batch_lot_number: str
    complaint_category: str
    status: ComplaintStatus
    created_at: datetime
    similarity_score: int = Field(ge=0, le=100)
    match_level: DuplicateMatchLevel
    match_reasons: list[str] = Field(min_length=1, max_length=5)


class DuplicateCheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    matches: list[DuplicateMatch] = Field(max_length=5)
    possible_match_threshold: int = Field(ge=0, le=100)
    strong_match_threshold: int = Field(ge=0, le=100)


RcaText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
]

RCA_CAPA_DISCLAIMER = (
    "AI-generated investigation-support recommendations for authorised QA review. "
    "Root causes are unconfirmed hypotheses and CAPA actions are not approved or "
    "implemented until evaluated through the organisation's quality system."
)

PROHIBITED_RCA_CLAIMS = (
    re.compile(r"\b(?:the )?root cause (?:is|was|has been) confirmed\b", re.I),
    re.compile(r"\bconfirmed root cause\b", re.I),
    re.compile(r"\binvestigation (?:is|was|has been) complet(?:e|ed)\b", re.I),
    re.compile(r"\bCAPA (?:is|was|has been) (?:approved|implemented|closed)\b", re.I),
    re.compile(r"\b(?:release|reject|recall) (?:the )?(?:batch|product)\b", re.I),
)


class PotentialRootCause(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    statement: RcaText
    rationale: RcaText
    evidence_required: RcaText


class CorrectiveAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action: RcaText
    purpose: RcaText
    verification: RcaText


class PreventiveAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action: RcaText
    purpose: RcaText
    effectiveness_check: RcaText


class RcaCapaRecommendations(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    potential_root_causes: list[PotentialRootCause] = Field(min_length=1, max_length=5)
    investigation_areas: list[RcaText] = Field(min_length=1, max_length=8)
    corrective_actions: list[CorrectiveAction] = Field(min_length=1, max_length=5)
    preventive_actions: list[PreventiveAction] = Field(min_length=1, max_length=5)
    assumptions_or_limitations: list[RcaText] = Field(min_length=1, max_length=8)
    human_review_required: Literal[True] = True
    disclaimer: str = RCA_CAPA_DISCLAIMER

    @model_validator(mode="before")
    @classmethod
    def enforce_trusted_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                **data,
                "human_review_required": True,
                "disclaimer": RCA_CAPA_DISCLAIMER,
            }
        return data

    @model_validator(mode="after")
    def reject_final_decisions(self) -> Self:
        text = " ".join(
            str(value) for value in self.model_dump(exclude={"disclaimer"}).values()
        )
        if any(pattern.search(text) for pattern in PROHIBITED_RCA_CLAIMS):
            raise ValueError("RCA/CAPA output contains a prohibited final claim")
        return self
