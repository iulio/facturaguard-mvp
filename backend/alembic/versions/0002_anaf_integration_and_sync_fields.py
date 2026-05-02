"""anaf integration and sync fields

Revision ID: 0002_anaf_integration
Revises: 0001_initial_schema
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_anaf_integration"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("invoices", sa.Column("anaf_upload_id", sa.String(length=120), nullable=True))
    op.add_column("invoices", sa.Column("last_synced_at", sa.DateTime(), nullable=True))

    op.create_table(
        "organization_integrations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="anaf"),
        sa.Column("mode", sa.String(length=40), nullable=False, server_default="mock"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="not_configured"),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_org_integrations_org_id", "organization_integrations", ["organization_id"])

def downgrade() -> None:
    op.drop_index("ix_org_integrations_org_id", table_name="organization_integrations")
    op.drop_table("organization_integrations")
    op.drop_column("invoices", "last_synced_at")
    op.drop_column("invoices", "anaf_upload_id")
