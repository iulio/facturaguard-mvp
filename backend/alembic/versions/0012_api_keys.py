"""api keys

Revision ID: 0012_api_keys
Revises: 0011_invoice_metadata
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012_api_keys"
down_revision: Union[str, None] = "0011_invoice_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("key_prefix", sa.String(length=24), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("scopes", sa.String(length=500), nullable=False, server_default="invoices:write"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_api_keys_org_id", "api_keys", ["organization_id"])
    op.create_index("ix_api_keys_prefix", "api_keys", ["key_prefix"])

def downgrade() -> None:
    op.drop_index("ix_api_keys_prefix", table_name="api_keys")
    op.drop_index("ix_api_keys_org_id", table_name="api_keys")
    op.drop_table("api_keys")
