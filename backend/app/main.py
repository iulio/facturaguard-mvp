from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI, File, Header, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .access import get_accessible_organization, write_audit_log
from .bulk_actions_service import run_bulk_invoice_action
from .client_portal_service import get_client_portal_detail, get_client_portal_organizations
from .billing import assert_can_create_organization, assert_can_import_invoices, assert_can_store_document, get_or_create_subscription, get_usage, list_plans, update_subscription_plan
from .api_keys_service import authenticate_api_key, create_api_key, list_api_keys, revoke_api_key
from .audit_service import audit_logs_to_csv, filter_audit_logs
from .auth import create_access_token, get_current_user, hash_password, verify_password
from sqlalchemy import text
from .database import Base, engine, get_db
from .jobs import run_status_check, start_scheduler, stop_scheduler
from .digest_service import build_daily_digest, send_daily_digest
from .file_storage import read_document_content, store_upload_file
from .invoice_metadata_service import update_invoice_metadata
from .invoice_notes_service import create_invoice_note, list_invoice_notes
from .invitation_service import accept_invitation, create_invitation, get_public_invitation
from .middleware import InMemoryRateLimitMiddleware, RequestTimingMiddleware
from .models import Alert, ApiKey, AuditLog, Invoice, InvoiceNote, Organization, OrganizationDocument, OrganizationIntegration, OrganizationInvitation, OrganizationMember, OrganizationNotificationSettings, OrganizationSubscription, PaymentTransaction, SavedView, User
from .parsers import parse_csv_upload, parse_xml_upload, parse_zip_upload
from .schemas import (
    AlertOut,
    ApiInvoiceCreate,
    ApiKeyCreate,
    ApiKeyCreatedOut,
    ApiKeyOut,
    AuditLogOut,
    BulkInvoiceActionIn,
    BulkInvoiceActionResult,
    AuditSummaryOut,
    CheckoutCreateIn,
    ClientPortalOrganizationDetailOut,
    ClientPortalSummaryOut,
    CheckoutSessionOut,
    DashboardSummary,
    DigestPreviewOut,
    DigestSendResult,
    InvoiceMetadataOut,
    InvoiceMetadataUpdateIn,
    InvoiceNoteCreate,
    InvoiceNoteOut,
    InvoiceOut,
    InvitationAcceptIn,
    InvitationAcceptOut,
    InvitationAcceptWithAccountIn,
    InvitationAcceptWithAccountOut,
    InvitationCreate,
    InvitationOut,
    PlanOut,
    PublicInvitationOut,
    SavedViewCreate,
    SavedViewOut,
    SavedViewUpdate,
    LoginIn,
    MessageOut,
    MonthlyReport,
    NotificationSettingsOut,
    NotificationSettingsUpdateIn,
    OnboardingStatusOut,
    NetopiaMockWebhookIn,
    PasswordChangeIn,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
    PortfolioSummary,
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationDocumentOut,
    OrganizationMemberOut,
    OrganizationOut,
    IntegrationOut,
    IntegrationTestOut,
    BulkInvoiceSyncResult,
    InvoiceSyncResult,
    TokenOut,
    UserCreate,
    SubscriptionOut,
    SubscriptionUpdateIn,
    SystemStatusOut,
    UsageOut,
    UserOut,
    WorkQueueSummaryOut,
)
from .settings import get_settings
from .services import (
    build_monthly_report,
    compute_internal_status,
    create_alert_for_invoice,
    explain_anaf_error,
)
from .notification_settings_service import get_or_create_notification_settings, update_notification_settings
from .onboarding_service import build_onboarding_status
from .password_service import change_password, create_password_reset_token, reset_password_with_token
from .payment_service import create_netopia_mock_checkout, process_netopia_mock_webhook
from .portfolio_service import build_portfolio_summary
from .report_service import generate_invoices_csv, generate_monthly_report_pdf
from .saved_views_service import create_saved_view, delete_saved_view, list_saved_views, update_saved_view
from .work_queue_service import build_work_queue
from .system_status_service import build_system_status
from .template_service import CSV_TEMPLATE, XML_TEMPLATE, build_templates_zip
from .sync_service import (
    get_or_create_anaf_integration,
    sync_invoice_status,
    sync_organization_invoices,
    test_anaf_connection,
)

settings = get_settings()

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(RequestTimingMiddleware)
app.add_middleware(InMemoryRateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"app": settings.app_name, "version": settings.app_version, "status": "ok"}




@app.get("/templates/invoices.csv")
def download_csv_template():
    return Response(
        content=CSV_TEMPLATE,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="facturaguard-template.csv"'},
    )

@app.get("/templates/invoices.xml")
def download_xml_template():
    return Response(
        content=XML_TEMPLATE,
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="facturaguard-template.xml"'},
    )

@app.get("/templates/facturaguard-import-templates.zip")
def download_templates_zip():
    return Response(
        content=build_templates_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="facturaguard-import-templates.zip"'},
    )

@app.get("/system/status", response_model=SystemStatusOut)
def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_system_status(db)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }

@app.get("/ready")
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        return {"status": "not_ready", "database": "error", "detail": str(exc)}



@app.get("/billing/plans", response_model=list[PlanOut])
def get_billing_plans():
    return list_plans()

@app.post("/auth/register", response_model=TokenOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Există deja un cont cu acest email.")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="accountant",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenOut(access_token=create_access_token(user.email))

@app.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email sau parolă incorectă.")

    return TokenOut(access_token=create_access_token(user.email))

@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/auth/password-reset/request", response_model=MessageOut)
def request_password_reset(
    payload: PasswordResetRequestIn,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()

    # Do not reveal whether the email exists.
    if user:
        create_password_reset_token(db, user)
        db.commit()

    return MessageOut(message="Dacă emailul există, am trimis instrucțiuni de resetare.")

@app.post("/auth/password-reset/confirm", response_model=MessageOut)
def confirm_password_reset(
    payload: PasswordResetConfirmIn,
    db: Session = Depends(get_db),
):
    try:
        reset_password_with_token(db, payload.token, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    return MessageOut(message="Parola a fost resetată.")

@app.post("/auth/password-change", response_model=MessageOut)
def change_current_user_password(
    payload: PasswordChangeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        change_password(db, current_user, payload.current_password, payload.new_password)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    db.commit()
    return MessageOut(message="Parola a fost schimbată.")




@app.get("/onboarding/status", response_model=OnboardingStatusOut)
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_onboarding_status(db, current_user)


@app.get("/client-portal", response_model=ClientPortalSummaryOut)
def get_client_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClientPortalSummaryOut(
        organizations=get_client_portal_organizations(db, current_user)
    )

@app.get("/client-portal/organizations/{org_id}", response_model=ClientPortalOrganizationDetailOut)
def get_client_portal_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_client_portal_detail(db, current_user, org_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@app.get("/saved-views", response_model=list[SavedViewOut])
def get_saved_views(
    view_type: str = "portfolio",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_saved_views(db, current_user, view_type=view_type)

@app.post("/saved-views", response_model=SavedViewOut)
def create_user_saved_view(
    payload: SavedViewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved_view = create_saved_view(
        db,
        current_user,
        name=payload.name,
        view_type=payload.view_type,
        filters=payload.filters,
        is_default=payload.is_default,
    )
    db.commit()
    db.refresh(saved_view)
    return saved_view

@app.put("/saved-views/{saved_view_id}", response_model=SavedViewOut)
def update_user_saved_view(
    saved_view_id: int,
    payload: SavedViewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        saved_view = update_saved_view(
            db,
            current_user,
            saved_view_id=saved_view_id,
            name=payload.name,
            filters=payload.filters,
            is_default=payload.is_default,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    db.commit()
    db.refresh(saved_view)
    return saved_view

@app.delete("/saved-views/{saved_view_id}")
def delete_user_saved_view(
    saved_view_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_saved_view(db, current_user, saved_view_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    db.commit()
    return {"message": "Saved view deleted."}

@app.get("/portfolio", response_model=PortfolioSummary)
def portfolio_dashboard(
    risk: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_risks = {None, "high", "medium", "low"}
    if risk not in allowed_risks:
        raise HTTPException(status_code=400, detail="Risk must be one of: high, medium, low.")

    return build_portfolio_summary(db, current_user, risk=risk, search=search)

@app.post("/organizations", response_model=OrganizationOut)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        assert_can_create_organization(db, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    org = Organization(
        owner_user_id=current_user.id,
        name=payload.name,
        cui=payload.cui,
        address=payload.address,
    )
    db.add(org)
    db.flush()

    db.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=current_user.id,
            role="accountant_owner",
            status="active",
        )
    )
    get_or_create_subscription(db, org)

    write_audit_log(
        db,
        organization_id=org.id,
        actor_user_id=current_user.id,
        action="organization.created",
        entity_type="organization",
        entity_id=org.id,
        message=f"Firma {org.name} a fost creată.",
    )

    db.commit()
    db.refresh(org)
    return org

@app.get("/organizations", response_model=list[OrganizationOut])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owned_ids = [org.id for org in db.query(Organization).filter(Organization.owner_user_id == current_user.id).all()]
    member_ids = [
        membership.organization_id
        for membership in db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id, OrganizationMember.status == "active")
        .all()
    ]
    ids = sorted(set(owned_ids + member_ids))
    if not ids:
        return []
    return db.query(Organization).filter(Organization.id.in_(ids)).all()


@app.post("/organizations/{org_id}/invitations", response_model=InvitationOut)
def invite_organization_member(
    org_id: int,
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)

    try:
        invitation = create_invitation(
            db,
            organization=organization,
            invited_email=str(payload.email),
            role=payload.role,
            invited_by=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(invitation)
    return invitation

@app.get("/organizations/{org_id}/invitations", response_model=list[InvitationOut])
def list_organization_invitations(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user, require_owner=True)
    return (
        db.query(OrganizationInvitation)
        .filter(OrganizationInvitation.organization_id == org_id)
        .order_by(OrganizationInvitation.created_at.desc())
        .all()
    )


@app.get("/invitations/public/{token}", response_model=PublicInvitationOut)
def get_public_invitation_details(
    token: str,
    db: Session = Depends(get_db),
):
    try:
        invitation = get_public_invitation(db, token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    organization = db.query(Organization).filter(Organization.id == invitation.organization_id).first()

    return PublicInvitationOut(
        organization_name=organization.name if organization else "",
        invited_email=invitation.invited_email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
    )

@app.post("/invitations/accept-with-account", response_model=InvitationAcceptWithAccountOut)
def accept_invitation_with_account(
    payload: InvitationAcceptWithAccountIn,
    db: Session = Depends(get_db),
):
    try:
        invitation = get_public_invitation(db, payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    existing_user = db.query(User).filter(User.email == invitation.invited_email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Există deja un cont cu acest email. Autentifică-te și acceptă invitația din cont.",
        )

    user = User(
        name=payload.name,
        email=invitation.invited_email,
        password_hash=hash_password(payload.password),
        role="client",
    )
    db.add(user)
    db.flush()

    try:
        invitation, member = accept_invitation(db, payload.token, user)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    organization = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    access_token = create_access_token(user.email)

    db.commit()

    return InvitationAcceptWithAccountOut(
        access_token=access_token,
        organization_id=invitation.organization_id,
        organization_name=organization.name if organization else "",
        role=member.role,
        status=invitation.status,
    )

@app.post("/invitations/accept", response_model=InvitationAcceptOut)
def accept_organization_invitation(
    payload: InvitationAcceptIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        invitation, member = accept_invitation(db, payload.token, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    organization = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    db.commit()

    return InvitationAcceptOut(
        organization_id=invitation.organization_id,
        organization_name=organization.name if organization else "",
        role=member.role,
        status=invitation.status,
    )

@app.post("/organizations/{org_id}/members", response_model=OrganizationMemberOut)
def add_organization_member(
    org_id: int,
    payload: OrganizationMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)

    allowed_roles = {"client_viewer", "client_operator", "accountant_owner"}
    if payload.role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Rol invalid. Alege unul din: {', '.join(sorted(allowed_roles))}")

    target_user = db.query(User).filter(User.email == payload.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilizatorul invitat trebuie să aibă deja cont în MVP.")

    existing = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == target_user.id,
        )
        .first()
    )
    if existing:
        existing.role = payload.role
        existing.status = "active"
        member = existing
    else:
        member = OrganizationMember(
            organization_id=org_id,
            user_id=target_user.id,
            role=payload.role,
            status="active",
        )
        db.add(member)
        db.flush()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=current_user.id,
        action="member.upserted",
        entity_type="organization_member",
        entity_id=member.id,
        message=f"Utilizatorul {target_user.email} a primit rolul {payload.role}.",
    )

    db.commit()
    db.refresh(member)
    return member



@app.get("/organizations/{org_id}/api-keys", response_model=list[ApiKeyOut])
def get_api_keys(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)
    return list_api_keys(db, organization)

@app.post("/organizations/{org_id}/api-keys", response_model=ApiKeyCreatedOut)
def create_organization_api_key(
    org_id: int,
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)
    api_key, raw_key = create_api_key(
        db,
        organization=organization,
        actor=current_user,
        name=payload.name,
        scopes=payload.scopes,
    )
    db.commit()
    db.refresh(api_key)
    return ApiKeyCreatedOut(
        id=api_key.id,
        organization_id=api_key.organization_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        status=api_key.status,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )

@app.post("/organizations/{org_id}/api-keys/{api_key_id}/revoke", response_model=ApiKeyOut)
def revoke_organization_api_key(
    org_id: int,
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)

    try:
        api_key = revoke_api_key(db, organization, current_user, api_key_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    db.commit()
    db.refresh(api_key)
    return api_key

@app.post("/public-api/v1/invoices", response_model=InvoiceOut)
def public_api_create_invoice(
    payload: ApiInvoiceCreate,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    try:
        api_key = authenticate_api_key(db, x_api_key or "", required_scope="invoices:write")
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    organization = db.query(Organization).filter(Organization.id == api_key.organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organizația nu există.")

    internal_status, due_date = compute_internal_status(payload.issue_date, payload.anaf_status)
    invoice = Invoice(
        organization_id=organization.id,
        invoice_number=payload.invoice_number,
        issue_date=payload.issue_date,
        due_submission_date=due_date,
        customer_name=payload.customer_name,
        customer_cui=payload.customer_cui,
        total_amount=payload.total_amount,
        currency=payload.currency,
        source="public_api",
        internal_status=internal_status,
        anaf_status=payload.anaf_status,
        anaf_message=payload.anaf_message,
        plain_explanation=explain_anaf_error(payload.anaf_message),
    )
    db.add(invoice)
    db.flush()

    create_alert_for_invoice(db, organization, invoice, notify_email=None)

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=None,
        action="public_api.invoice_created",
        entity_type="invoice",
        entity_id=invoice.id,
        message=f"Factura {invoice.invoice_number} a fost creată prin API public.",
    )

    db.commit()
    db.refresh(invoice)
    return invoice

@app.get("/organizations/{org_id}/work-queue", response_model=WorkQueueSummaryOut)
def get_work_queue(
    org_id: int,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)
    return build_work_queue(
        db,
        organization=organization,
        status=status,
        priority=priority,
        tag=tag,
        limit=limit,
    )

@app.get("/organizations/{org_id}/dashboard", response_model=DashboardSummary)
def organization_dashboard(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
    open_alerts = (
        db.query(Alert)
        .filter(Alert.organization_id == org_id, Alert.status == "open")
        .count()
    )

    return DashboardSummary(
        total_invoices=len(invoices),
        validated=sum(1 for i in invoices if i.internal_status == "validated"),
        rejected=sum(1 for i in invoices if i.internal_status == "rejected"),
        unsent=sum(1 for i in invoices if i.internal_status == "unsent"),
        near_deadline=sum(1 for i in invoices if i.internal_status == "near_deadline"),
        overdue=sum(1 for i in invoices if i.internal_status == "overdue"),
        open_alerts=open_alerts,
    )


@app.post("/organizations/{org_id}/invoices/bulk-action", response_model=BulkInvoiceActionResult)
def bulk_invoice_action(
    org_id: int,
    payload: BulkInvoiceActionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_write=True)

    try:
        result = run_bulk_invoice_action(
            db,
            organization=organization,
            actor=current_user,
            invoice_ids=payload.invoice_ids,
            action=payload.action,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    return result



@app.put("/organizations/{org_id}/invoices/{invoice_id}/metadata", response_model=InvoiceMetadataOut)
def update_invoice_metadata_endpoint(
    org_id: int,
    invoice_id: int,
    payload: InvoiceMetadataUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_write=True)
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.organization_id == org_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura nu a fost găsită.")

    try:
        updated = update_invoice_metadata(
            db,
            organization=organization,
            invoice=invoice,
            actor=current_user,
            tags=payload.tags,
            priority=payload.priority,
            assignee_user_id=payload.assignee_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(updated)
    return updated

@app.get("/organizations/{org_id}/invoices/{invoice_id}/notes", response_model=list[InvoiceNoteOut])
def get_invoice_notes(
    org_id: int,
    invoice_id: int,
    include_internal: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.organization_id == org_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura nu a fost găsită.")

    return list_invoice_notes(db, organization, invoice, include_internal=include_internal)

@app.post("/organizations/{org_id}/invoices/{invoice_id}/notes", response_model=InvoiceNoteOut)
def add_invoice_note(
    org_id: int,
    invoice_id: int,
    payload: InvoiceNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_write=True)
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.organization_id == org_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura nu a fost găsită.")

    try:
        note = create_invoice_note(
            db,
            organization=organization,
            invoice=invoice,
            actor=current_user,
            body=payload.body,
            is_internal=payload.is_internal,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(note)
    return note

@app.get("/organizations/{org_id}/invoices", response_model=list[InvoiceOut])
def list_invoices(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    return (
        db.query(Invoice)
        .filter(Invoice.organization_id == org_id)
        .order_by(Invoice.issue_date.desc())
        .all()
    )

@app.post("/organizations/{org_id}/invoices/upload", response_model=list[InvoiceOut])
async def upload_invoices(
    org_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_write=True)
    content = await file.read()
    filename = file.filename.lower()

    try:
        assert_can_store_document(db, organization)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    document = store_upload_file(
        db,
        organization=organization,
        upload_file=file,
        content=content,
        actor=current_user,
        document_type="invoice_import",
    )

    try:
        if filename.endswith(".csv"):
            parsed = parse_csv_upload(content)
            source = "csv"
        elif filename.endswith(".xml"):
            parsed = parse_xml_upload(content)
            source = "xml"
        elif filename.endswith(".zip"):
            parsed = parse_zip_upload(content)
            source = "zip"
        else:
            raise HTTPException(status_code=400, detail="Acceptăm momentan doar CSV, XML sau ZIP.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Fișier invalid: {exc}")

    try:
        assert_can_import_invoices(db, organization, len(parsed))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    created = []
    for item in parsed:
        internal_status, due_date = compute_internal_status(
            item["issue_date"],
            item.get("anaf_status"),
        )
        invoice = Invoice(
            organization_id=org_id,
            invoice_number=item["invoice_number"],
            issue_date=item["issue_date"],
            due_submission_date=due_date,
            customer_name=item["customer_name"],
            customer_cui=item["customer_cui"],
            total_amount=item["total_amount"],
            currency=item.get("currency", "RON"),
            source=source,
            internal_status=internal_status,
            anaf_status=item.get("anaf_status", "pending"),
            anaf_message=item.get("anaf_message"),
            plain_explanation=explain_anaf_error(item.get("anaf_message")),
        )
        db.add(invoice)
        db.flush()
        create_alert_for_invoice(db, organization, invoice, notify_email=current_user.email)
        created.append(invoice)

    write_audit_log(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="invoices.uploaded",
        entity_type="invoice_batch",
        message=f"Au fost importate {len(created)} facturi din fișierul {file.filename}. Document ID: {document.id}.",
    )

    db.commit()
    for invoice in created:
        db.refresh(invoice)

    return created




@app.post("/organizations/{org_id}/billing/netopia-mock/checkout", response_model=CheckoutSessionOut)
def create_netopia_mock_checkout_session(
    org_id: int,
    payload: CheckoutCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)

    try:
        transaction = create_netopia_mock_checkout(db, organization, payload.plan_code, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(transaction)
    return transaction

@app.get("/organizations/{org_id}/billing/transactions", response_model=list[CheckoutSessionOut])
def list_payment_transactions(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user, require_owner=True)
    return (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.organization_id == org_id)
        .order_by(PaymentTransaction.created_at.desc())
        .all()
    )

@app.post("/billing/netopia-mock/webhook", response_model=CheckoutSessionOut)
def netopia_mock_webhook(
    payload: NetopiaMockWebhookIn,
    db: Session = Depends(get_db),
):
    try:
        transaction = process_netopia_mock_webhook(
            db,
            session_id=payload.session_id,
            status=payload.status,
            secret=payload.secret,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(transaction)
    return transaction



@app.get("/organizations/{org_id}/digest/preview", response_model=DigestPreviewOut)
def preview_daily_digest(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)
    settings = get_or_create_notification_settings(db, organization, default_email=current_user.email)
    recipient = settings.alert_email or current_user.email
    return build_daily_digest(db, organization, recipient)

@app.post("/organizations/{org_id}/digest/send", response_model=DigestSendResult)
def send_daily_digest_now(
    org_id: int,
    force: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)
    result = send_daily_digest(db, organization, actor=current_user, force=force)
    db.commit()
    return result

@app.get("/organizations/{org_id}/notification-settings", response_model=NotificationSettingsOut)
def get_notification_settings(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)
    settings = get_or_create_notification_settings(db, organization, default_email=current_user.email)
    db.commit()
    db.refresh(settings)
    return settings

@app.put("/organizations/{org_id}/notification-settings", response_model=NotificationSettingsOut)
def update_organization_notification_settings(
    org_id: int,
    payload: NotificationSettingsUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)
    settings = get_or_create_notification_settings(db, organization, default_email=current_user.email)
    update_notification_settings(settings, payload.model_dump(exclude_unset=True))

    write_audit_log(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="notification_settings.updated",
        entity_type="organization_notification_settings",
        entity_id=settings.id,
        message="Setările de notificare au fost actualizate.",
    )

    db.commit()
    db.refresh(settings)
    return settings

@app.get("/organizations/{org_id}/subscription", response_model=SubscriptionOut)
def get_organization_subscription(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)
    subscription = get_or_create_subscription(db, organization)
    db.commit()
    db.refresh(subscription)
    return subscription

@app.post("/organizations/{org_id}/subscription", response_model=SubscriptionOut)
def update_organization_subscription(
    org_id: int,
    payload: SubscriptionUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_owner=True)

    try:
        subscription = update_subscription_plan(db, organization, payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    write_audit_log(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="subscription.updated",
        entity_type="organization_subscription",
        entity_id=subscription.id,
        message=f"Planul organizației a fost schimbat la {payload.plan_code}.",
    )

    db.commit()
    db.refresh(subscription)
    return subscription

@app.get("/organizations/{org_id}/usage", response_model=UsageOut)
def get_organization_usage(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)
    return get_usage(db, organization)

@app.get("/organizations/{org_id}/integrations/anaf", response_model=IntegrationOut)
def get_anaf_integration(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)
    integration = get_or_create_anaf_integration(db, organization.id)
    db.commit()
    db.refresh(integration)
    return integration

@app.post("/organizations/{org_id}/integrations/anaf/test", response_model=IntegrationTestOut)
def test_anaf_integration(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_write=True)
    integration = test_anaf_connection(db, organization, actor=current_user)
    db.commit()
    return IntegrationTestOut(
        provider=integration.provider,
        mode=integration.mode,
        status=integration.status,
        message="Mock ANAF connector tested successfully.",
    )

@app.post("/organizations/{org_id}/invoices/{invoice_id}/sync-status", response_model=InvoiceSyncResult)
def sync_single_invoice_status(
    org_id: int,
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_write=True)
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.organization_id == org_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura nu a fost găsită.")

    result = sync_invoice_status(db, organization, invoice, actor=current_user)
    db.commit()
    return result

@app.post("/organizations/{org_id}/invoices/sync-statuses", response_model=BulkInvoiceSyncResult)
def sync_all_invoice_statuses(
    org_id: int,
    only_open: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user, require_write=True)
    result = sync_organization_invoices(db, organization, actor=current_user, only_open=only_open)
    db.commit()
    return result

@app.get("/organizations/{org_id}/alerts", response_model=list[AlertOut])
def list_alerts(
    org_id: int,
    status: str | None = "open",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    query = db.query(Alert).filter(Alert.organization_id == org_id)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).all()

@app.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nu a fost găsită.")

    get_accessible_organization(db, alert.organization_id, current_user, require_write=True)

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()

    write_audit_log(
        db,
        organization_id=alert.organization_id,
        actor_user_id=current_user.id,
        action="alert.resolved",
        entity_type="alert",
        entity_id=alert.id,
        message=f"Alerta {alert.title} a fost rezolvată.",
    )

    db.commit()
    db.refresh(alert)
    return alert

@app.get("/organizations/{org_id}/reports/monthly", response_model=MonthlyReport)
def monthly_report(
    org_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
    return build_monthly_report(org_id, year, month, invoices)


@app.get("/organizations/{org_id}/reports/monthly.pdf")
def monthly_report_pdf(
    org_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)
    invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
    pdf_bytes = generate_monthly_report_pdf(organization, year, month, invoices)

    filename = f"facturaguard-report-{organization.cui}-{year}-{month:02d}.pdf"
    write_audit_log(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="report.pdf_generated",
        entity_type="monthly_report",
        entity_id=f"{year}-{month:02d}",
        message=f"Raportul PDF pentru {year}-{month:02d} a fost generat.",
    )
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.get("/organizations/{org_id}/invoices/export.csv")
def export_invoices_csv(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)
    invoices = (
        db.query(Invoice)
        .filter(Invoice.organization_id == org_id)
        .order_by(Invoice.issue_date.desc())
        .all()
    )
    csv_content = generate_invoices_csv(invoices)

    write_audit_log(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="invoices.csv_exported",
        entity_type="invoice_export",
        message=f"Export CSV generat pentru {len(invoices)} facturi.",
    )
    db.commit()

    filename = f"facturaguard-invoices-{organization.cui}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/organizations/{org_id}/documents", response_model=list[OrganizationDocumentOut])
def list_organization_documents(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    return (
        db.query(OrganizationDocument)
        .filter(OrganizationDocument.organization_id == org_id)
        .order_by(OrganizationDocument.created_at.desc())
        .all()
    )

@app.get("/organizations/{org_id}/documents/{document_id}/download")
def download_organization_document(
    org_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    document = (
        db.query(OrganizationDocument)
        .filter(
            OrganizationDocument.id == document_id,
            OrganizationDocument.organization_id == org_id,
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Documentul nu a fost găsit.")

    try:
        content = read_document_content(document)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    write_audit_log(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="document.downloaded",
        entity_type="organization_document",
        entity_id=document.id,
        message=f"Documentul {document.original_filename} a fost descărcat.",
    )
    db.commit()

    return Response(
        content=content,
        media_type=document.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{document.original_filename}"'},
    )

@app.get("/organizations/{org_id}/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    org_id: int,
    action: str | None = None,
    entity_type: str | None = None,
    actor_user_id: int | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    return filter_audit_logs(
        db,
        organization_id=org_id,
        action=action,
        entity_type=entity_type,
        actor_user_id=actor_user_id,
        limit=limit,
    )

@app.get("/organizations/{org_id}/audit-logs/export.csv")
def export_audit_logs_csv(
    org_id: int,
    action: str | None = None,
    entity_type: str | None = None,
    actor_user_id: int | None = None,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = get_accessible_organization(db, org_id, current_user)

    logs = filter_audit_logs(
        db,
        organization_id=org_id,
        action=action,
        entity_type=entity_type,
        actor_user_id=actor_user_id,
        limit=limit,
    )
    csv_content = audit_logs_to_csv(logs)

    write_audit_log(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="audit.csv_exported",
        entity_type="audit_export",
        message=f"Audit CSV exportat cu {len(logs)} evenimente.",
    )
    db.commit()

    filename = f"facturaguard-audit-{organization.cui}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.get("/organizations/{org_id}/audit-summary", response_model=AuditSummaryOut)
def get_audit_summary(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(1000)
        .all()
    )

    by_action: dict[str, int] = {}
    by_entity_type: dict[str, int] = {}

    for log in logs:
        by_action[log.action] = by_action.get(log.action, 0) + 1
        entity = log.entity_type or "unknown"
        by_entity_type[entity] = by_entity_type.get(entity, 0) + 1

    return AuditSummaryOut(
        organization_id=org_id,
        total_events=len(logs),
        by_action=[
            {"action": action, "count": count}
            for action, count in sorted(by_action.items(), key=lambda item: item[1], reverse=True)
        ][:20],
        by_entity_type=[
            {"entity_type": entity_type, "count": count}
            for entity_type, count in sorted(by_entity_type.items(), key=lambda item: item[1], reverse=True)
        ][:20],
        recent_events=logs[:10],
    )

@app.post("/jobs/run-status-check")
def manual_status_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = run_status_check(db)
    return result
