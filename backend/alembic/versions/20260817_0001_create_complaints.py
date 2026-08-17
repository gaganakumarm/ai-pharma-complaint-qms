"""create complaints ledger

Revision ID: 20260817_0001
Revises:
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260817_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    source_type = postgresql.ENUM(
        "MANUAL", "TEXT", "PDF", name="source_type", create_type=False
    )
    product_type = postgresql.ENUM(
        "API", "FDF", "UNKNOWN", name="product_type", create_type=False
    )
    severity = postgresql.ENUM(
        "MINOR", "MAJOR", "CRITICAL", name="complaint_severity", create_type=False
    )
    complaint_status = postgresql.ENUM(
        "PENDING_TRIAGE",
        "READY_TO_COMMIT",
        "COMMITTED",
        name="complaint_status",
        create_type=False,
    )
    source_type.create(op.get_bind())
    product_type.create(op.get_bind())
    severity.create(op.get_bind())
    complaint_status.create(op.get_bind())
    op.execute("CREATE SEQUENCE complaint_number_seq START WITH 1")
    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "complaint_number",
            sa.String(length=32),
            server_default=sa.text(
                "'CMP-' || to_char(CURRENT_DATE, 'YYYY') || '-' || "
                "lpad(nextval('complaint_number_seq')::text, 6, '0')"
            ),
            nullable=False,
        ),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("complaint_source", sa.String(length=255)),
        sa.Column("customer_name", sa.String(length=200), nullable=False),
        sa.Column("product_type", product_type, nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("product_strength_grade", sa.String(length=100)),
        sa.Column("batch_lot_number", sa.String(length=100), nullable=False),
        sa.Column("affected_quantity", sa.String(length=100)),
        sa.Column("manufacturing_date", sa.String(length=100)),
        sa.Column("expiry_retest_date", sa.String(length=100)),
        sa.Column("originating_site_block", sa.String(length=200)),
        sa.Column("impacted_non_product_materials", sa.Text()),
        sa.Column("complaint_category", sa.String(length=150), nullable=False),
        sa.Column("complaint_description", sa.Text(), nullable=False),
        sa.Column("suggested_severity", severity),
        sa.Column("initial_risk_assessment", sa.Text()),
        sa.Column("suggested_next_action", sa.Text()),
        sa.Column("status", complaint_status, nullable=False),
        sa.Column("raw_input", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_number"),
    )
    op.create_index(
        "ix_complaints_complaint_number", "complaints", ["complaint_number"]
    )
    op.create_index(
        "ix_complaints_batch_lot_number", "complaints", ["batch_lot_number"]
    )
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])
    op.create_index(
        "ix_complaints_product_name_lower",
        "complaints",
        [sa.text("lower(product_name)")],
    )


def downgrade() -> None:
    op.drop_table("complaints")
    op.execute("DROP SEQUENCE complaint_number_seq")
    for enum_name in (
        "complaint_status",
        "complaint_severity",
        "product_type",
        "source_type",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind())
