"""payment transactions

Revision ID: 0007_payment_transactions
Revises: 0006_subscriptions
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_payment_transactions"
down_revision: Union[str, None] = "0006_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="netopia_mock"),
        sa.Column("provider_session_id", sa.String(length=120), nullable=False),
        sa.Column("plan_code", sa.String(length=50), nullable=False),
        sa.Column("amount_eur", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("checkout_url", sa.String(length=500), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_payment_transactions_org_id", "payment_transactions", ["organization_id"])
    op.create_index("ix_payment_transactions_session", "payment_transactions", ["provider_session_id"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_payment_transactions_session", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_org_id", table_name="payment_transactions")
    op.drop_table("payment_transactions")
