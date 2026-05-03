from datetime import date, datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class OrganizationCreate(BaseModel):
    name: str
    cui: str
    address: str | None = None

class OrganizationOut(BaseModel):
    id: int
    name: str
    cui: str
    address: str | None = None

    class Config:
        from_attributes = True

class OrganizationMemberCreate(BaseModel):
    email: EmailStr
    role: str = "client_viewer"

class OrganizationMemberOut(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceOut(BaseModel):
    id: int
    organization_id: int
    invoice_number: str
    issue_date: date
    due_submission_date: date
    customer_name: str
    customer_cui: str
    total_amount: float
    currency: str
    source: str
    internal_status: str
    anaf_status: str
    anaf_message: str | None = None
    plain_explanation: str | None = None
    anaf_upload_id: str | None = None
    last_synced_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    organization_id: int
    invoice_id: int | None
    alert_type: str
    severity: str
    title: str
    message: str
    status: str
    sent_email: bool
    created_at: datetime
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: int
    organization_id: int
    actor_user_id: int | None
    action: str
    entity_type: str | None
    entity_id: str | None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardSummary(BaseModel):
    total_invoices: int
    validated: int
    rejected: int
    unsent: int
    near_deadline: int
    overdue: int
    open_alerts: int

class MonthlyReport(BaseModel):
    organization_id: int
    year: int
    month: int
    total_invoices: int
    validated: int
    rejected: int
    unsent: int
    near_deadline: int
    overdue: int
    total_amount: float
    top_errors: list[dict]
    recommendations: list[str]


class IntegrationOut(BaseModel):
    id: int
    organization_id: int
    provider: str
    mode: str
    status: str
    config_json: str | None = None
    last_checked_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class IntegrationTestOut(BaseModel):
    provider: str
    mode: str
    status: str
    message: str

class InvoiceSyncResult(BaseModel):
    invoice_id: int
    invoice_number: str
    old_status: str
    new_status: str
    changed: bool
    message: str | None = None

class BulkInvoiceSyncResult(BaseModel):
    organization_id: int
    checked: int
    changed: int
    results: list[InvoiceSyncResult]


class PortfolioOrganizationSummary(BaseModel):
    organization_id: int
    name: str
    cui: str
    total_invoices: int
    validated: int
    rejected: int
    unsent: int
    near_deadline: int
    overdue: int
    open_alerts: int
    risk_score: int
    risk_label: str

class PortfolioSummary(BaseModel):
    total_organizations: int
    high_risk: int
    medium_risk: int
    low_risk: int
    total_open_alerts: int
    organizations: list[PortfolioOrganizationSummary]


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = "client_viewer"

class InvitationOut(BaseModel):
    id: int
    organization_id: int
    invited_email: EmailStr
    role: str
    token: str
    status: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class InvitationAcceptIn(BaseModel):
    token: str

class InvitationAcceptOut(BaseModel):
    organization_id: int
    organization_name: str
    role: str
    status: str


class PublicInvitationOut(BaseModel):
    organization_name: str
    invited_email: EmailStr
    role: str
    status: str
    expires_at: datetime

class InvitationAcceptWithAccountIn(BaseModel):
    token: str
    name: str
    password: str

class InvitationAcceptWithAccountOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    organization_id: int
    organization_name: str
    role: str
    status: str


class PasswordResetRequestIn(BaseModel):
    email: EmailStr

class PasswordResetConfirmIn(BaseModel):
    token: str
    new_password: str

class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str

class MessageOut(BaseModel):
    message: str


class OrganizationDocumentOut(BaseModel):
    id: int
    organization_id: int
    uploaded_by_user_id: int | None
    original_filename: str
    stored_filename: str
    content_type: str | None
    file_size: int
    document_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PlanOut(BaseModel):
    code: str
    name: str
    monthly_price_eur: float
    max_organizations: int
    max_invoices_per_month: int
    max_documents: int
    features: list[str]

class SubscriptionOut(BaseModel):
    id: int
    organization_id: int
    plan_code: str
    status: str
    billing_provider: str | None = None
    billing_customer_id: str | None = None
    billing_subscription_id: str | None = None
    current_period_end: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SubscriptionUpdateIn(BaseModel):
    plan_code: str

class UsageOut(BaseModel):
    organization_id: int
    plan_code: str
    invoices_this_month: int
    documents_total: int
    max_invoices_per_month: int
    max_documents: int


class CheckoutCreateIn(BaseModel):
    plan_code: str

class CheckoutSessionOut(BaseModel):
    id: int
    organization_id: int
    provider: str
    provider_session_id: str
    plan_code: str
    amount_eur: float
    currency: str
    status: str
    checkout_url: str | None = None
    created_at: datetime
    paid_at: datetime | None = None

    class Config:
        from_attributes = True

class NetopiaMockWebhookIn(BaseModel):
    session_id: str
    status: str
    secret: str


class OnboardingStatusOut(BaseModel):
    has_organization: bool
    organization_id: int | None = None
    organization_name: str | None = None
    has_invoices: bool
    invoice_count: int
    has_run_sync: bool
    open_alerts: int
    completed: bool
    next_step: str


class AuditSummaryOut(BaseModel):
    organization_id: int
    total_events: int
    by_action: list[dict]
    by_entity_type: list[dict]
    recent_events: list[AuditLogOut]


class NotificationSettingsOut(BaseModel):
    id: int
    organization_id: int
    email_alerts_enabled: bool
    alert_email: str | None = None
    send_rejected_alerts: bool
    send_overdue_alerts: bool
    send_near_deadline_alerts: bool
    near_deadline_days: int
    daily_digest_enabled: bool
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationSettingsUpdateIn(BaseModel):
    email_alerts_enabled: bool | None = None
    alert_email: EmailStr | None = None
    send_rejected_alerts: bool | None = None
    send_overdue_alerts: bool | None = None
    send_near_deadline_alerts: bool | None = None
    near_deadline_days: int | None = None
    daily_digest_enabled: bool | None = None


class DigestPreviewOut(BaseModel):
    organization_id: int
    recipient: str | None
    subject: str
    body: str
    would_send: bool

class DigestSendResult(BaseModel):
    organization_id: int
    sent: bool
    recipient: str | None
    message: str
