import pytest
from pydantic import ValidationError

from app.domain import ProductType
from app.schemas import ComplaintCreate


def valid_payload() -> dict[str, str]:
    return {
        "customer_name": " Acme Hospitals ",
        "product_name": " Paracetamol ",
        "batch_lot_number": " LOT-001 ",
        "complaint_category": " Packaging ",
        "complaint_description": " Seal was damaged ",
    }


def test_schema_trims_text() -> None:
    complaint = ComplaintCreate.model_validate(valid_payload())
    assert complaint.customer_name == "Acme Hospitals"
    assert complaint.batch_lot_number == "LOT-001"


@pytest.mark.parametrize("field", list(valid_payload()))
def test_schema_rejects_blank_required_values(field: str) -> None:
    payload = valid_payload()
    payload[field] = "   "
    with pytest.raises(ValidationError):
        ComplaintCreate.model_validate(payload)


def test_schema_rejects_invalid_enum_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ComplaintCreate.model_validate(
            {**valid_payload(), "product_type": "BIOLOGIC", "unexpected": True}
        )
    assert (
        ComplaintCreate.model_validate(valid_payload()).product_type
        is ProductType.UNKNOWN
    )
