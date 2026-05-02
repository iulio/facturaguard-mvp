"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="accountant"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("cui", sa.String(length=50), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_organizations_cui", "organizations", ["cui"])

    op.create_table(
        "organization_members",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="client_viewer"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_org_members_org_id", "organization_members", ["organization_id"])
    op.create_index("ix_org_members_user_id", "organization_members", ["user_id"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_submission_date", sa.Date(), nullable=False),
        sa.Column("customer_name", sa.String(length=200), nullable=False),
        sa.Column("customer_cui", sa.String(length=50), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="RON"),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="manual"),
        sa.Column("internal_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("anaf_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("anaf_message", sa.Text(), nullable=True),
        sa.Column("plain_explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="medium"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("sent_email", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_organization_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("alerts")
    op.drop_index("ix_invoices_invoice_number", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_org_members_user_id", table_name="organization_members")
    op.drop_index("ix_org_members_org_id", table_name="organization_members")
    op.drop_table("organization_members")
    op.drop_index("ix_organizations_cui", table_name="organizations")
    op.drop_table("organizations")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
