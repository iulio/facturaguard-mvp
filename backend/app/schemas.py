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
    tags: str | None = None
    priority: str = "normal"
    assignee_user_id: int | None = None
    anaf_upload_id: str | None = None
    anaf_download_id: str | None = None
    anaf_response_document_id: int | None = None
    anaf_last_checked_at: datetime | None = None
    anaf_submission_environment: str | None = None
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
    provider_order_id: str | None = None
    provider_payment_id: str | None = None
    provider_status: str | None = None
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


class ClientPortalOrganizationOut(BaseModel):
    id: int
    name: str
    cui: str
    role: str
    total_invoices: int
    open_alerts: int
    rejected: int
    overdue: int
    near_deadline: int

class ClientPortalSummaryOut(BaseModel):
    organizations: list[ClientPortalOrganizationOut]

class ClientPortalOrganizationDetailOut(BaseModel):
    organization: ClientPortalOrganizationOut
    recent_invoices: list[InvoiceOut]
    open_alerts: list[AlertOut]
    documents: list[OrganizationDocumentOut]


class SavedViewCreate(BaseModel):
    name: str
    view_type: str = "portfolio"
    filters: dict = {}
    is_default: bool = False

class SavedViewUpdate(BaseModel):
    name: str | None = None
    filters: dict | None = None
    is_default: bool | None = None

class SavedViewOut(BaseModel):
    id: int
    user_id: int
    name: str
    view_type: str
    filters_json: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkInvoiceActionIn(BaseModel):
    invoice_ids: list[int]
    action: str

class BulkInvoiceActionResult(BaseModel):
    organization_id: int
    action: str
    requested: int
    processed: int
    skipped: int
    message: str


class InvoiceNoteCreate(BaseModel):
    body: str
    is_internal: bool = False

class InvoiceNoteOut(BaseModel):
    id: int
    organization_id: int
    invoice_id: int
    author_user_id: int | None
    body: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceMetadataUpdateIn(BaseModel):
    tags: str | None = None
    priority: str | None = None
    assignee_user_id: int | None = None

class InvoiceMetadataOut(BaseModel):
    id: int
    tags: str | None = None
    priority: str
    assignee_user_id: int | None = None

    class Config:
        from_attributes = True


class WorkQueueSummaryOut(BaseModel):
    organization_id: int
    total: int
    urgent: int
    high: int
    rejected: int
    overdue: int
    near_deadline: int
    invoices: list[InvoiceOut]


class SystemStatusOut(BaseModel):
    app_name: str
    app_version: str
    environment: str
    database: str
    scheduler_enabled: bool
    email_dry_run: bool
    storage_backend: str
    anaf_connector_mode: str
    netopia_mock_enabled: bool
    rate_limit_enabled: bool
    total_organizations: int
    total_invoices: int
    total_documents: int
    total_open_alerts: int


class ApiKeyCreate(BaseModel):
    name: str
    scopes: str = "invoices:write"

class ApiKeyOut(BaseModel):
    id: int
    organization_id: int
    name: str
    key_prefix: str
    scopes: str
    status: str
    last_used_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApiKeyCreatedOut(ApiKeyOut):
    raw_key: str

class ApiInvoiceCreate(BaseModel):
    invoice_number: str
    issue_date: date
    customer_name: str
    customer_cui: str
    total_amount: float
    currency: str = "RON"
    anaf_status: str = "pending"
    anaf_message: str | None = None


class AnafConnectOut(BaseModel):
    authorization_url: str
    state: str
    mode: str

class AnafConfigCheckOut(BaseModel):
    mode: str
    environment: str
    auth_base: str
    api_base: str
    redirect_uri: str | None
    configured: bool
    missing_variables: list[str]

class AnafAuthorizationOut(BaseModel):
    id: int
    organization_id: int
    authorized_cif: str
    token_type: str
    expires_at: datetime | None = None
    scope: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    last_refresh_at: datetime | None = None

    class Config:
        from_attributes = True


class UblPreviewOut(BaseModel):
    invoice_id: int
    invoice_number: str
    filename: str
    xml: str
    warning: str


class AnafUploadDraftResult(BaseModel):
    invoice_id: int
    invoice_number: str
    environment: str
    attempted: bool
    uploaded: bool
    anaf_upload_id: str | None = None
    message: str
    raw_response: str | None = None


class AnafStatusCheckResult(BaseModel):
    invoice_id: int
    invoice_number: str
    environment: str
    attempted: bool
    checked: bool
    anaf_upload_id: str | None = None
    anaf_status: str | None = None
    internal_status: str | None = None
    message: str
    raw_response: str | None = None


class AnafDownloadResponseResult(BaseModel):
    invoice_id: int
    invoice_number: str
    environment: str
    attempted: bool
    downloaded: bool
    anaf_download_id: str | None = None
    document_id: int | None = None
    filename: str | None = None
    message: str
    size_bytes: int | None = None


class AnafParsedResponseOut(BaseModel):
    invoice_id: int
    invoice_number: str
    document_id: int
    applied: bool
    file_count: int
    xml_file_count: int
    summary_status: str
    summary_message: str
    files: list[dict]


class NetopiaConfigCheckOut(BaseModel):
    provider: str
    mode: str
    base_url: str
    configured: bool
    missing_variables: list[str]
    notify_url: str | None = None
    redirect_url: str | None = None
    cancel_url: str | None = None
    currency: str

class NetopiaWebhookResultOut(BaseModel):
    transaction_id: int | None = None
    provider: str
    provider_order_id: str | None = None
    provider_payment_id: str | None = None
    status: str
    message: str


class NetopiaStatusCheckOut(BaseModel):
    transaction_id: int
    organization_id: int
    provider: str
    provider_order_id: str | None = None
    provider_payment_id: str | None = None
    previous_status: str
    current_status: str
    provider_status: str | None = None
    changed: bool
    message: str
    raw_response: dict | None = None
