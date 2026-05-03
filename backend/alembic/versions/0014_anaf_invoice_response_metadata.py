"""anaf invoice response metadata

Revision ID: 0014_anaf_invoice_response_metadata
Revises: 0013_anaf_authorizations
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014_anaf_invoice_response_metadata"
down_revision: Union[str, None] = "0013_anaf_authorizations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("invoices", sa.Column("anaf_download_id", sa.String(length=120), nullable=True))
    # SQLite CI compatibility: no FK constraint in ALTER TABLE.
    op.add_column("invoices", sa.Column("anaf_response_document_id", sa.Integer(), nullable=True))
    op.add_column("invoices", sa.Column("anaf_last_checked_at", sa.DateTime(), nullable=True))
    op.add_column("invoices", sa.Column("anaf_submission_environment", sa.String(length=20), nullable=True))

def downgrade() -> None:
    op.drop_column("invoices", "anaf_submission_environment")
    op.drop_column("invoices", "anaf_last_checked_at")
    op.drop_column("invoices", "anaf_response_document_id")
    op.drop_column("invoices", "anaf_download_id")
