import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain import ComplaintSeverity, ComplaintStatus, ProductType, SourceType

RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ComplaintCreate(BaseModel):
    """Manual commit payload; five core complaint fields are required."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_type: SourceType = SourceType.MANUAL
    complaint_source: str | None = Field(default=None, max_length=255)
    customer_name: RequiredText = Field(max_length=200)
    product_type: ProductType = ProductType.UNKNOWN
    product_name: RequiredText = Field(max_length=200)
    product_strength_grade: str | None = Field(default=None, max_length=100)
    batch_lot_number: RequiredText = Field(max_length=100)
    affected_quantity: str | None = Field(default=None, max_length=100)
    manufacturing_date: str | None = Field(default=None, max_length=100)
    expiry_retest_date: str | None = Field(default=None, max_length=100)
    originating_site_block: str | None = Field(default=None, max_length=200)
    impacted_non_product_materials: str | None = Field(default=None, max_length=2000)
    complaint_category: RequiredText = Field(max_length=150)
    complaint_description: RequiredText = Field(max_length=5000)
    suggested_severity: ComplaintSeverity | None = None
    initial_risk_assessment: str | None = Field(default=None, max_length=5000)
    suggested_next_action: str | None = Field(default=None, max_length=5000)
    raw_input: str | None = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def normalize_optional_blanks(self) -> Self:
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, str) and not isinstance(value, Enum):
                stripped = value.strip()
                setattr(self, field_name, stripped or None)
        return self


class ComplaintResponse(ComplaintCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_number: str
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime


class ComplaintListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_number: str
    customer_name: str
    product_name: str
    batch_lot_number: str
    complaint_category: str
    status: ComplaintStatus
    created_at: datetime


class PaginatedComplaintResponse(BaseModel):
    items: list[ComplaintListItem]
    page: int
    page_size: int
    total: int
    total_pages: int
