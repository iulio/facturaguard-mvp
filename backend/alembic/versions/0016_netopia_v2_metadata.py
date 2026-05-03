"""netopia v2 metadata

Revision ID: 0016_netopia_v2_metadata
Revises: 0015_rename_free_plan_to_one
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016_netopia_v2_metadata"
down_revision: Union[str, None] = "0015_rename_free_plan_to_one"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("payment_transactions", sa.Column("provider_order_id", sa.String(length=160), nullable=True))
    op.add_column("payment_transactions", sa.Column("provider_payment_id", sa.String(length=160), nullable=True))
    op.add_column("payment_transactions", sa.Column("provider_status", sa.String(length=80), nullable=True))
    op.create_index("ix_payment_transactions_provider_order_id", "payment_transactions", ["provider_order_id"])
    op.create_index("ix_payment_transactions_provider_payment_id", "payment_transactions", ["provider_payment_id"])

def downgrade() -> None:
    op.drop_index("ix_payment_transactions_provider_payment_id", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_provider_order_id", table_name="payment_transactions")
    op.drop_column("payment_transactions", "provider_status")
    op.drop_column("payment_transactions", "provider_payment_id")
    op.drop_column("payment_transactions", "provider_order_id")
