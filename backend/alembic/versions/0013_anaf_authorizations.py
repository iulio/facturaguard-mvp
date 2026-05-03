"""anaf authorizations

Revision ID: 0013_anaf_authorizations
Revises: 0012_api_keys
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013_anaf_authorizations"
down_revision: Union[str, None] = "0012_api_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "anaf_authorizations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("authorized_cif", sa.String(length=50), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=30), nullable=False, server_default="Bearer"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("scope", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_refresh_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_anaf_authorizations_org_id", "anaf_authorizations", ["organization_id"])
    op.create_index("ix_anaf_authorizations_cif", "anaf_authorizations", ["authorized_cif"])

def downgrade() -> None:
    op.drop_index("ix_anaf_authorizations_cif", table_name="anaf_authorizations")
    op.drop_index("ix_anaf_authorizations_org_id", table_name="anaf_authorizations")
    op.drop_table("anaf_authorizations")
