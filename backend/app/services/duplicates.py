import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol

from app.infrastructure.database.models import ComplaintModel
from app.schemas.enhancements import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    DuplicateMatch,
    DuplicateMatchLevel,
)

POSSIBLE_MATCH_THRESHOLD = 45
STRONG_MATCH_THRESHOLD = 75
CANDIDATE_LIMIT = 50
RESULT_LIMIT = 5


def normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").casefold())


def similarity(left: str | None, right: str | None) -> float:
    a, b = normalize(left), normalize(right)
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


class DuplicateCandidateSource(Protocol):
    async def find_duplicate_candidates(
        self, request: DuplicateCheckRequest, limit: int
    ) -> list[ComplaintModel]: ...


@dataclass(frozen=True)
class ScoredCandidate:
    record: ComplaintModel
    score: int
    reasons: list[str]


class DuplicateScorer:
    def score(
        self, draft: DuplicateCheckRequest, candidate: ComplaintModel
    ) -> ScoredCandidate:
        batch_exact = bool(normalize(draft.batch_lot_number)) and normalize(
            draft.batch_lot_number
        ) == normalize(candidate.batch_lot_number)
        product = similarity(draft.product_name, candidate.product_name)
        category = similarity(draft.complaint_category, candidate.complaint_category)
        description = similarity(
            draft.complaint_description, candidate.complaint_description
        )
        quantity = similarity(draft.affected_quantity, candidate.affected_quantity)
        score = round(
            (40 if batch_exact else 0)
            + product * 30
            + category * 12
            + description * 13
            + quantity * 5
        )
        reasons: list[str] = []
        if batch_exact:
            reasons.append("Exact normalized batch/lot match")
        if product >= 0.85:
            reasons.append("Highly similar product name")
        if category >= 0.75:
            reasons.append("Similar complaint category")
        if description >= 0.65:
            reasons.append("Similar complaint description")
        if quantity >= 0.9:
            reasons.append("Matching affected quantity")
        return ScoredCandidate(candidate, max(0, min(100, score)), reasons)


class DuplicateDetectionService:
    def __init__(
        self, source: DuplicateCandidateSource, scorer: DuplicateScorer | None = None
    ) -> None:
        self.source = source
        self.scorer = scorer or DuplicateScorer()

    async def check(self, request: DuplicateCheckRequest) -> DuplicateCheckResponse:
        candidates = await self.source.find_duplicate_candidates(
            request, CANDIDATE_LIMIT
        )
        scored = [self.scorer.score(request, candidate) for candidate in candidates]
        ranked = sorted(
            (item for item in scored if item.score >= POSSIBLE_MATCH_THRESHOLD),
            key=lambda item: (
                -item.score,
                -item.record.created_at.timestamp(),
                str(item.record.id),
            ),
        )[:RESULT_LIMIT]
        return DuplicateCheckResponse(
            matches=[
                DuplicateMatch(
                    complaint_id=item.record.id,
                    complaint_number=item.record.complaint_number,
                    product_name=item.record.product_name,
                    batch_lot_number=item.record.batch_lot_number,
                    complaint_category=item.record.complaint_category,
                    status=item.record.status,
                    created_at=item.record.created_at,
                    similarity_score=item.score,
                    match_level=(
                        DuplicateMatchLevel.STRONG_MATCH
                        if item.score >= STRONG_MATCH_THRESHOLD
                        else DuplicateMatchLevel.POSSIBLE_MATCH
                    ),
                    match_reasons=item.reasons or ["Combined field similarity"],
                )
                for item in ranked
            ],
            possible_match_threshold=POSSIBLE_MATCH_THRESHOLD,
            strong_match_threshold=STRONG_MATCH_THRESHOLD,
        )
