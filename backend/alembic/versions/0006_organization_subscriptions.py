"""organization subscriptions

Revision ID: 0006_subscriptions
Revises: 0005_documents
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_subscriptions"
down_revision: Union[str, None] = "0005_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "organization_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan_code", sa.String(length=50), nullable=False, server_default="one"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("billing_provider", sa.String(length=80), nullable=True),
        sa.Column("billing_customer_id", sa.String(length=120), nullable=True),
        sa.Column("billing_subscription_id", sa.String(length=120), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_org_subscriptions_org_id", "organization_subscriptions", ["organization_id"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_org_subscriptions_org_id", table_name="organization_subscriptions")
    op.drop_table("organization_subscriptions")
