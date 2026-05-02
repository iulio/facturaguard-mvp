from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .access import get_accessible_organization, write_audit_log
from .auth import create_access_token, get_current_user, hash_password, verify_password
from sqlalchemy import text
from .database import Base, engine, get_db
from .jobs import run_status_check, start_scheduler, stop_scheduler
from .invitation_service import accept_invitation, create_invitation
from .middleware import InMemoryRateLimitMiddleware, RequestTimingMiddleware
from .models import Alert, AuditLog, Invoice, Organization, OrganizationIntegration, OrganizationInvitation, OrganizationMember, User
from .parsers import parse_csv_upload, parse_xml_upload, parse_zip_upload
from .schemas import (
    AlertOut,
    AuditLogOut,
    DashboardSummary,
    InvoiceOut,
    InvitationAcceptIn,
    InvitationAcceptOut,
    InvitationCreate,
    InvitationOut,
    LoginIn,
    MonthlyReport,
    PortfolioSummary,
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberOut,
    OrganizationOut,
    IntegrationOut,
    IntegrationTestOut,
    BulkInvoiceSyncResult,
    InvoiceSyncResult,
    TokenOut,
    UserCreate,
    UserOut,
)
from .settings import get_settings
from .services import (
    build_monthly_report,
    compute_internal_status,
    create_alert_for_invoice,
    explain_anaf_error,
)
from .portfolio_service import build_portfolio_summary
from .report_service import generate_invoices_csv, generate_monthly_report_pdf
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
        message=f"Au fost importate {len(created)} facturi din fișierul {file.filename}.",
    )

    db.commit()
    for invoice in created:
        db.refresh(invoice)

    return created


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

@app.get("/organizations/{org_id}/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_organization(db, org_id, current_user)
    return (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )

@app.post("/jobs/run-status-check")
def manual_status_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = run_status_check(db)
    return result
