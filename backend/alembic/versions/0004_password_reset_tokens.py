"""password reset tokens

Revision ID: 0004_password_resets
Revises: 0003_invitations
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_password_resets"
down_revision: Union[str, None] = "0003_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_password_reset_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_password_reset_token", "password_reset_tokens", ["token"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_password_reset_token", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
