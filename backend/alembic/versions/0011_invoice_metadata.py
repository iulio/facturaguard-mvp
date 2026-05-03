"""invoice metadata

Revision ID: 0011_invoice_metadata
Revises: 0010_invoice_notes
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_invoice_metadata"
down_revision: Union[str, None] = "0010_invoice_notes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("invoices", sa.Column("tags", sa.String(length=500), nullable=True))
    op.add_column("invoices", sa.Column("priority", sa.String(length=30), nullable=False, server_default="normal"))
    # SQLite, used by CI, does not support adding a FK constraint via ALTER TABLE.
    # Keep the application-level relationship in SQLAlchemy models, but add the
    # column without a DB-level FK in this migration for cross-dialect compatibility.
    op.add_column("invoices", sa.Column("assignee_user_id", sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column("invoices", "assignee_user_id")
    op.drop_column("invoices", "priority")
    op.drop_column("invoices", "tags")
