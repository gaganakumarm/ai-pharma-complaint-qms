from dataclasses import dataclass

from app.schemas.correction import (
    ComplaintCorrectionPatch,
    CorrectableComplaint,
    CorrectionField,
)


@dataclass(frozen=True)
class CorrectionMergeResult:
    complaint: CorrectableComplaint
    changed_fields: list[CorrectionField]


def merge_correction(
    current: CorrectableComplaint, patch: ComplaintCorrectionPatch
) -> CorrectionMergeResult:
    values = current.model_dump()
    changed: list[CorrectionField] = []
    for update in patch.updates:
        value: object = update.value
        if update.field is CorrectionField.PRODUCT_TYPE and value is not None:
            value = str(value).upper()
        if values[update.field.value] != value:
            values[update.field.value] = value
            changed.append(update.field)
    return CorrectionMergeResult(CorrectableComplaint.model_validate(values), changed)
