"""rename free plan to one

Revision ID: 0015_rename_free_plan_to_one
Revises: 0014_anaf_invoice_response_metadata
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0015_rename_free_plan_to_one"
down_revision: Union[str, None] = "0014_anaf_invoice_response_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("UPDATE organization_subscriptions SET plan_code = 'one' WHERE plan_code = 'free'")
    op.execute("UPDATE payment_transactions SET plan_code = 'one' WHERE plan_code = 'free'")

def downgrade() -> None:
    op.execute("UPDATE organization_subscriptions SET plan_code = 'free' WHERE plan_code = 'one'")
    op.execute("UPDATE payment_transactions SET plan_code = 'free' WHERE plan_code = 'one'")
