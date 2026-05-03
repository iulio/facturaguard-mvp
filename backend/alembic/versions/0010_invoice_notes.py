"""invoice notes

Revision ID: 0010_invoice_notes
Revises: 0009_saved_views
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010_invoice_notes"
down_revision: Union[str, None] = "0009_saved_views"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "invoice_notes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("author_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_invoice_notes_org_id", "invoice_notes", ["organization_id"])
    op.create_index("ix_invoice_notes_invoice_id", "invoice_notes", ["invoice_id"])

def downgrade() -> None:
    op.drop_index("ix_invoice_notes_invoice_id", table_name="invoice_notes")
    op.drop_index("ix_invoice_notes_org_id", table_name="invoice_notes")
    op.drop_table("invoice_notes")
