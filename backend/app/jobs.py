import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Invoice, Organization, User
from .services import compute_internal_status, create_alert_for_invoice

scheduler: BackgroundScheduler | None = None

def run_status_check(db: Session | None = None) -> dict:
    owns_session = db is None
    if db is None:
        db = SessionLocal()
    checked = changed = alerts = 0
    try:
        invoices = db.query(Invoice).all()
        for invoice in invoices:
            checked += 1
            old_status = invoice.internal_status
            new_status, due_date = compute_internal_status(invoice.issue_date, invoice.anaf_status)
            invoice.due_submission_date = due_date
            if old_status != new_status:
                invoice.internal_status = new_status
                invoice.updated_at = datetime.utcnow()
                changed += 1
            org = db.query(Organization).filter(Organization.id == invoice.organization_id).first()
            if org:
                owner = db.query(User).filter(User.id == org.owner_user_id).first()
                alert = create_alert_for_invoice(db, org, invoice, notify_email=owner.email if owner else None)
                if alert:
                    alerts += 1
        db.commit()
        return {"checked": checked, "changed": changed, "alerts_created_or_existing": alerts, "ran_at": datetime.utcnow().isoformat()}
    finally:
        if owns_session:
            db.close()

def start_scheduler():
    global scheduler
    if os.getenv("FG_ENABLE_SCHEDULER", "true").lower() == "false":
        print("FacturaGuard scheduler dezactivat.")
        return None
    if scheduler and scheduler.running:
        return scheduler
    interval = int(os.getenv("FG_STATUS_CHECK_INTERVAL_MINUTES", "60"))
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(run_status_check, "interval", minutes=interval, id="facturaguard_status_check", replace_existing=True)
    scheduler.start()
    print(f"FacturaGuard scheduler pornit. Interval: {interval} minute.")
    return scheduler

def stop_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("FacturaGuard scheduler oprit.")
