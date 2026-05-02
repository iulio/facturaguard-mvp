"""organization invitations

Revision ID: 0003_invitations
Revises: 0002_anaf_integration
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_invitations"
down_revision: Union[str, None] = "0002_anaf_integration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "organization_invitations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("invited_email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="client_viewer"),
        sa.Column("token", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("invited_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_org_invites_org_id", "organization_invitations", ["organization_id"])
    op.create_index("ix_org_invites_email", "organization_invitations", ["invited_email"])
    op.create_index("ix_org_invites_token", "organization_invitations", ["token"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_org_invites_token", table_name="organization_invitations")
    op.drop_index("ix_org_invites_email", table_name="organization_invitations")
    op.drop_index("ix_org_invites_org_id", table_name="organization_invitations")
    op.drop_table("organization_invitations")
