"""organization documents

Revision ID: 0005_documents
Revises: 0004_password_resets
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_documents"
down_revision: Union[str, None] = "0004_password_resets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "organization_documents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("document_type", sa.String(length=60), nullable=False, server_default="upload"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="stored"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_org_documents_org_id", "organization_documents", ["organization_id"])

def downgrade() -> None:
    op.drop_index("ix_org_documents_org_id", table_name="organization_documents")
    op.drop_table("organization_documents")
