import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Sequence, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain import ComplaintSeverity, ComplaintStatus, ProductType, SourceType
from app.infrastructure.database.base import Base

complaint_number_sequence = Sequence("complaint_number_seq")


class ComplaintModel(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        Index("ix_complaints_batch_lot_number", "batch_lot_number"),
        Index("ix_complaints_product_name_lower", func.lower(text("product_name"))),
        Index("ix_complaints_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
        server_default=text(
            "'CMP-' || to_char(CURRENT_DATE, 'YYYY') || '-' || "
            "lpad(nextval('complaint_number_seq')::text, 6, '0')"
        ),
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type"), nullable=False
    )
    complaint_source: Mapped[str | None] = mapped_column(String(255))
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_type: Mapped[ProductType] = mapped_column(
        Enum(ProductType, name="product_type"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_strength_grade: Mapped[str | None] = mapped_column(String(100))
    batch_lot_number: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_quantity: Mapped[str | None] = mapped_column(String(100))
    manufacturing_date: Mapped[str | None] = mapped_column(String(100))
    expiry_retest_date: Mapped[str | None] = mapped_column(String(100))
    originating_site_block: Mapped[str | None] = mapped_column(String(200))
    impacted_non_product_materials: Mapped[str | None] = mapped_column(Text)
    complaint_category: Mapped[str] = mapped_column(String(150), nullable=False)
    complaint_description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_severity: Mapped[ComplaintSeverity | None] = mapped_column(
        Enum(ComplaintSeverity, name="complaint_severity")
    )
    initial_risk_assessment: Mapped[str | None] = mapped_column(Text)
    suggested_next_action: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status"), nullable=False
    )
    raw_input: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
