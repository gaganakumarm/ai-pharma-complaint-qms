from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain import ProductType, SourceType
from app.schemas.assessment import ComplaintQualityAssessment


class ExtractedComplaint(BaseModel):
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
    complaint_description: str | None = Field(max_length=5000)

    @model_validator(mode="before")
    @classmethod
    def normalize_empty_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: (value.strip() or None) if isinstance(value, str) else value
                for key, value in data.items()
            }
        return data


class ProcessTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)


class ProcessingStatus(StrEnum):
    PROCESSED = "PROCESSED"


class ProcessTextResponse(BaseModel):
    source_type: SourceType = SourceType.TEXT
    input_length: int
    extracted_complaint: ExtractedComplaint
    quality_assessment: ComplaintQualityAssessment
    warnings: list[str]
    assistant_message: str
    status: ProcessingStatus = ProcessingStatus.PROCESSED
    model: str


class DocumentMetadata(BaseModel):
    filename: str
    content_type: str
    page_count: int
    character_count: int


class ProcessDocumentResponse(BaseModel):
    source_type: SourceType = SourceType.PDF
    document: DocumentMetadata
    extracted_complaint: ExtractedComplaint
    quality_assessment: ComplaintQualityAssessment
    warnings: list[str]
    assistant_message: str
    status: ProcessingStatus = ProcessingStatus.PROCESSED
    model: str
