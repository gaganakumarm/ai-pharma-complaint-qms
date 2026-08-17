import re
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain import ComplaintSeverity

HUMAN_REVIEW_DISCLAIMER = (
    "AI-generated initial assessment for QA review. Final severity, investigation, "
    "batch disposition, CAPA, and market actions must be determined and approved by "
    "authorised quality personnel."
)

FORBIDDEN_DECISION_CLAIMS = (
    re.compile(r"\broot cause (?:is|was|has been) confirmed\b", re.IGNORECASE),
    re.compile(r"\bconfirmed root cause\b", re.IGNORECASE),
    re.compile(r"\binvestigation (?:is|was|has been) complet(?:e|ed)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:batch|product) (?:is|has been|should be) (?:approved|rejected)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:automatically |immediately )?"
        r"(?:initiate|approve|execute) (?:a )?recall\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bfinal approval\b", re.IGNORECASE),
)


class AssessmentStatus(StrEnum):
    COMPLETE = "COMPLETE"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"


InformationGap = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
]


class ComplaintQualityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    complaint_category: str = Field(min_length=1, max_length=150)
    structured_complaint_description: str = Field(min_length=1, max_length=5000)
    suggested_severity: ComplaintSeverity
    severity_rationale: str = Field(min_length=1, max_length=2000)
    initial_risk_assessment: str = Field(min_length=1, max_length=5000)
    suggested_next_action: str = Field(min_length=1, max_length=3000)
    assessment_status: AssessmentStatus
    information_gaps: list[InformationGap] = Field(default_factory=list, max_length=20)
    human_review_required: Literal[True] = True
    disclaimer: str = HUMAN_REVIEW_DISCLAIMER

    @model_validator(mode="before")
    @classmethod
    def enforce_trusted_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                **data,
                "human_review_required": True,
                "disclaimer": HUMAN_REVIEW_DISCLAIMER,
            }
        return data

    @model_validator(mode="after")
    def validate_safety_and_consistency(self) -> Self:
        if (
            self.assessment_status is AssessmentStatus.NEEDS_INFORMATION
            and not self.information_gaps
        ):
            raise ValueError("NEEDS_INFORMATION requires at least one information gap")
        if (
            self.assessment_status is AssessmentStatus.COMPLETE
            and self.information_gaps
        ):
            raise ValueError("COMPLETE assessment cannot contain information gaps")
        assessment_text = " ".join(
            (
                self.severity_rationale,
                self.initial_risk_assessment,
                self.suggested_next_action,
            )
        )
        if any(
            pattern.search(assessment_text) for pattern in FORBIDDEN_DECISION_CLAIMS
        ):
            raise ValueError("Assessment contains a forbidden final decision claim")
        return self
