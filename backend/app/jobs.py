from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Invoice, Organization, User
from .services import compute_internal_status, create_alert_for_invoice
from .settings import get_settings
from .digest_service import send_due_digests_for_all_organizations
from .sync_service import sync_organization_invoices

scheduler: BackgroundScheduler | None = None

def run_status_check(db: Session | None = None) -> dict:
    owns_session = db is None
    if db is None:
        db = SessionLocal()
    checked = changed = alerts = 0
    try:
        organizations = db.query(Organization).all()
        for org in organizations:
            owner = db.query(User).filter(User.id == org.owner_user_id).first()
            result = sync_organization_invoices(db, org, actor=owner, only_open=True)
            checked += result["checked"]
            changed += result["changed"]
            alerts += len([item for item in result["results"] if item.get("message")])
        db.commit()
        return {"checked": checked, "changed": changed, "alerts_created_or_existing": alerts, "ran_at": datetime.utcnow().isoformat()}
    finally:
        if owns_session:
            db.close()

def run_daily_digest_job() -> dict:
    db = SessionLocal()
    try:
        results = send_due_digests_for_all_organizations(db)
        db.commit()
        return {"sent_or_skipped": len(results), "ran_at": datetime.utcnow().isoformat()}
    finally:
        db.close()

def start_scheduler():
    global scheduler
    settings = get_settings()
    if not settings.fg_enable_scheduler:
        print("FacturaGuard scheduler dezactivat.")
        return None
    if scheduler and scheduler.running:
        return scheduler
    interval = settings.fg_status_check_interval_minutes
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(run_status_check, "interval", minutes=interval, id="facturaguard_status_check", replace_existing=True)
    scheduler.add_job(run_daily_digest_job, "cron", hour=8, minute=0, id="facturaguard_daily_digest", replace_existing=True)
    scheduler.start()
    print(f"FacturaGuard scheduler pornit. Interval: {interval} minute.")
    return scheduler

def stop_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("FacturaGuard scheduler oprit.")
