import copy
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.domain import ComplaintStatus
from app.schemas.enhancements import (
    RCA_CAPA_DISCLAIMER,
    DuplicateCheckRequest,
    RcaCapaRecommendations,
)
from app.services.completeness import ComplaintCompletenessChecker
from app.services.duplicates import (
    POSSIBLE_MATCH_THRESHOLD,
    STRONG_MATCH_THRESHOLD,
    DuplicateDetectionService,
    DuplicateScorer,
)


def complete_draft(**updates: object) -> dict[str, object]:
    draft: dict[str, object] = {
        "customer_name": "Fictional Customer",
        "product_type": "FDF",
        "product_name": "Amoxicillin Capsules",
        "product_strength_grade": "500 mg",
        "batch_lot_number": "LOT-1/A",
        "complaint_category": "Discoloration",
        "complaint_description": "Brown discoloration was observed.",
        "complaint_source": "Training email",
        "affected_quantity": "48 capsules",
        "manufacturing_date": "2026-01-01",
        "expiry_retest_date": "2028-01-01",
        "originating_site_block": "Site A",
        "impacted_non_product_materials": "None observed",
    }
    draft.update(updates)
    return draft


def candidate(**updates: object) -> SimpleNamespace:
    values = {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "complaint_number": "CMP-2026-000001",
        "product_name": "Amoxicillin Capsules",
        "batch_lot_number": "lot 1-a",
        "complaint_category": "Discoloration",
        "complaint_description": "Brown discoloration was observed in capsules.",
        "affected_quantity": "48 capsules",
        "status": ComplaintStatus.COMMITTED,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(updates)
    return SimpleNamespace(**values)


def duplicate_draft() -> DuplicateCheckRequest:
    draft = complete_draft()
    return DuplicateCheckRequest(
        **{
            field: draft[field]
            for field in DuplicateCheckRequest.model_fields
            if field in draft
        }
    )


def rca_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "potential_root_causes": [
            {
                "statement": "Packaging exposure may have contributed",
                "rationale": "Discoloration can require packaging review",
                "evidence_required": "Packaging integrity and stability data",
            }
        ],
        "investigation_areas": ["Packaging integrity"],
        "corrective_actions": [
            {
                "action": "Evaluate appropriate containment",
                "purpose": "Protect product while evidence is reviewed",
                "verification": "QA verifies documented completion",
            }
        ],
        "preventive_actions": [
            {
                "action": "Trend verified findings",
                "purpose": "Identify recurrence",
                "effectiveness_check": "Review the defined trend period",
            }
        ],
        "assumptions_or_limitations": ["Causality is not established"],
        "human_review_required": False,
        "disclaimer": "Untrusted model disclaimer",
    }
    payload.update(updates)
    return payload


@pytest.mark.parametrize(
    "field",
    [
        "customer_name",
        "product_name",
        "batch_lot_number",
        "complaint_category",
        "complaint_description",
    ],
)
def test_completeness_required_fields_and_input_immutability(field: str) -> None:
    checker = ComplaintCompletenessChecker()
    draft = complete_draft()
    original = copy.deepcopy(draft)
    assert checker.assess(draft).completeness_percentage == 100
    draft[field] = "  "
    result = checker.assess(draft)
    assert result.completeness_percentage == 80
    assert field in result.missing_required_fields
    assert original[field] != draft[field]


@pytest.mark.parametrize("placeholder", [None, "Unknown", "N/A", "Not provided"])
def test_completeness_rejects_placeholders(placeholder: str | None) -> None:
    result = ComplaintCompletenessChecker().assess(
        complete_draft(customer_name=placeholder)
    )
    assert result.status == "NEEDS_INFORMATION"
    assert result.required_fields_present == 4


def test_conditional_recommendations_use_existing_strength_grade() -> None:
    checker = ComplaintCompletenessChecker()
    for product_type in ("FDF", "API"):
        result = checker.assess(
            complete_draft(product_type=product_type, product_strength_grade=None)
        )
        assert "product_strength_grade" in result.missing_recommended_fields


def test_duplicate_score_normalizes_batch_and_is_bounded() -> None:
    draft = duplicate_draft()
    result = DuplicateScorer().score(draft, candidate())
    assert 0 <= result.score <= 100
    assert result.score >= STRONG_MATCH_THRESHOLD
    assert "Exact normalized batch/lot match" in result.reasons


def test_description_alone_is_not_a_possible_match() -> None:
    draft = DuplicateCheckRequest(
        product_name="Unrelated",
        batch_lot_number="OTHER",
        complaint_category="Other",
        complaint_description="Same words",
    )
    result = DuplicateScorer().score(
        draft,
        candidate(
            product_name="Different",
            batch_lot_number="LOT-X",
            complaint_category="Different",
            complaint_description="Same words",
        ),
    )
    assert result.score < POSSIBLE_MATCH_THRESHOLD


async def test_duplicate_ranking_is_deterministic_and_bounded() -> None:
    records = [candidate(id=uuid.UUID(int=index + 1)) for index in range(8)]

    class Source:
        async def find_duplicate_candidates(
            self, request: DuplicateCheckRequest, limit: int
        ) -> list[SimpleNamespace]:
            assert limit == 50
            return records

    result = await DuplicateDetectionService(Source()).check(duplicate_draft())
    assert len(result.matches) == 5
    assert [match.complaint_id.int for match in result.matches] == [1, 2, 3, 4, 5]


def test_rca_contract_forces_trusted_fields_and_rejects_extras() -> None:
    result = RcaCapaRecommendations.model_validate(rca_payload())
    assert result.human_review_required is True
    assert result.disclaimer == RCA_CAPA_DISCLAIMER
    with pytest.raises(ValidationError):
        RcaCapaRecommendations.model_validate(rca_payload(unknown="field"))


@pytest.mark.parametrize(
    "claim",
    [
        "The root cause is confirmed as packaging failure",
        "The investigation has been completed",
        "CAPA has been approved",
        "Recall the batch",
    ],
)
def test_rca_contract_rejects_prohibited_claims(claim: str) -> None:
    payload = rca_payload(assumptions_or_limitations=[claim])
    with pytest.raises(ValidationError):
        RcaCapaRecommendations.model_validate(payload)
