"""notification settings

Revision ID: 0008_notification_settings
Revises: 0007_payment_transactions
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_notification_settings"
down_revision: Union[str, None] = "0007_payment_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "organization_notification_settings",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("email_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("alert_email", sa.String(length=255), nullable=True),
        sa.Column("send_rejected_alerts", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("send_overdue_alerts", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("send_near_deadline_alerts", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("near_deadline_days", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("daily_digest_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_org_notification_settings_org_id", "organization_notification_settings", ["organization_id"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_org_notification_settings_org_id", table_name="organization_notification_settings")
    op.drop_table("organization_notification_settings")
