from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .auth import create_access_token, get_current_user, hash_password, verify_password
from .database import Base, engine, get_db
from .jobs import run_status_check, start_scheduler, stop_scheduler
from .models import Alert, Invoice, Organization, User
from .parsers import parse_csv_upload, parse_xml_upload, parse_zip_upload
from .schemas import AlertOut, DashboardSummary, InvoiceOut, LoginIn, MonthlyReport, OrganizationCreate, OrganizationOut, TokenOut, UserCreate, UserOut
from .services import build_monthly_report, compute_internal_status, create_alert_for_invoice, explain_anaf_error

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title="FacturaGuard MVP API", version="0.4.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"app": "FacturaGuard MVP API", "version": "0.4.0", "status": "ok"}

@app.post("/auth/register", response_model=TokenOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Există deja un cont cu acest email.")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password), role="accountant")
    db.add(user); db.commit(); db.refresh(user)
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

def get_owned_organization(org_id: int, db: Session, current_user: User) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id, Organization.owner_user_id == current_user.id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Firma nu a fost găsită.")
    return org

@app.post("/organizations", response_model=OrganizationOut)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    org = Organization(owner_user_id=current_user.id, name=payload.name, cui=payload.cui, address=payload.address)
    db.add(org); db.commit(); db.refresh(org)
    return org

@app.get("/organizations", response_model=list[OrganizationOut])
def list_organizations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Organization).filter(Organization.owner_user_id == current_user.id).all()

@app.get("/organizations/{org_id}/dashboard", response_model=DashboardSummary)
def organization_dashboard(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_owned_organization(org_id, db, current_user)
    invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
    open_alerts = db.query(Alert).filter(Alert.organization_id == org_id, Alert.status == "open").count()
    return DashboardSummary(total_invoices=len(invoices), validated=sum(1 for i in invoices if i.internal_status == "validated"), rejected=sum(1 for i in invoices if i.internal_status == "rejected"), unsent=sum(1 for i in invoices if i.internal_status == "unsent"), near_deadline=sum(1 for i in invoices if i.internal_status == "near_deadline"), overdue=sum(1 for i in invoices if i.internal_status == "overdue"), open_alerts=open_alerts)

@app.get("/organizations/{org_id}/invoices", response_model=list[InvoiceOut])
def list_invoices(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_owned_organization(org_id, db, current_user)
    return db.query(Invoice).filter(Invoice.organization_id == org_id).order_by(Invoice.issue_date.desc()).all()

@app.post("/organizations/{org_id}/invoices/upload", response_model=list[InvoiceOut])
async def upload_invoices(org_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    org = get_owned_organization(org_id, db, current_user)
    content = await file.read()
    filename = file.filename.lower()
    try:
        if filename.endswith(".csv"):
            parsed, source = parse_csv_upload(content), "csv"
        elif filename.endswith(".xml"):
            parsed, source = parse_xml_upload(content), "xml"
        elif filename.endswith(".zip"):
            parsed, source = parse_zip_upload(content), "zip"
        else:
            raise HTTPException(status_code=400, detail="Acceptăm momentan doar CSV, XML sau ZIP.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Fișier invalid: {exc}")

    created = []
    for item in parsed:
        internal_status, due_date = compute_internal_status(item["issue_date"], item.get("anaf_status"))
        invoice = Invoice(organization_id=org_id, invoice_number=item["invoice_number"], issue_date=item["issue_date"], due_submission_date=due_date, customer_name=item["customer_name"], customer_cui=item["customer_cui"], total_amount=item["total_amount"], currency=item.get("currency", "RON"), source=source, internal_status=internal_status, anaf_status=item.get("anaf_status", "pending"), anaf_message=item.get("anaf_message"), plain_explanation=explain_anaf_error(item.get("anaf_message")))
        db.add(invoice); db.flush()
        create_alert_for_invoice(db, org, invoice, notify_email=current_user.email)
        created.append(invoice)
    db.commit()
    for invoice in created:
        db.refresh(invoice)
    return created

@app.get("/organizations/{org_id}/alerts", response_model=list[AlertOut])
def list_alerts(org_id: int, status: str | None = "open", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_owned_organization(org_id, db, current_user)
    query = db.query(Alert).filter(Alert.organization_id == org_id)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).all()

@app.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(Alert).join(Organization, Organization.id == Alert.organization_id).filter(Alert.id == alert_id, Organization.owner_user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nu a fost găsită.")
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    db.commit(); db.refresh(alert)
    return alert

@app.get("/organizations/{org_id}/reports/monthly", response_model=MonthlyReport)
def monthly_report(org_id: int, year: int, month: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_owned_organization(org_id, db, current_user)
    invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
    return build_monthly_report(org_id, year, month, invoices)

@app.post("/jobs/run-status-check")
def manual_status_check(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return run_status_check(db)
