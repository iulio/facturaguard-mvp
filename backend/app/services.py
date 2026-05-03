from collections import Counter
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from .models import Alert, Invoice, Organization
from .notifier import send_email_notification
from .notification_settings_service import get_alert_recipient, get_or_create_notification_settings, should_send_alert_email

def add_business_days(start: date, business_days: int) -> date:
    current = start
    added = 0
    while added < business_days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current

def explain_anaf_error(raw_message: str | None) -> str | None:
    if not raw_message:
        return None
    m = raw_message.lower()
    if "cui" in m or "cod fiscal" in m or "companyid" in m:
        return "CUI-ul clientului pare invalid sau nu corespunde denumirii firmei. Verifică datele clientului."
    if "xml" in m or "schema" in m or "ubl" in m:
        return "Structura XML nu respectă formatul cerut. Regenerază factura din softul de facturare."
    if "spv" in m or "drept" in m or "certificat" in m or "token" in m:
        return "Există o problemă de acces SPV/certificat. Verifică drepturile de reprezentare pentru firmă."
    if "tva" in m or "vat" in m:
        return "Există o problemă legată de TVA. Verifică cotele, baza impozabilă și totalurile facturii."
    return "Factura are o eroare care trebuie verificată manual în mesajul ANAF."

def compute_internal_status(issue_date: date, anaf_status: str | None, today: date | None = None) -> tuple[str, date]:
    today = today or date.today()
    due_date = add_business_days(issue_date, 5)
    status = (anaf_status or "pending").lower().strip()
    if status == "validated":
        return "validated", due_date
    if status == "rejected":
        return "rejected", due_date
    if status == "unsent":
        if today > due_date:
            return "overdue", due_date
        if (due_date - today).days <= 2:
            return "near_deadline", due_date
        return "unsent", due_date
    if status in ["sent", "pending"]:
        if today > due_date:
            return "overdue", due_date
        return "pending", due_date
    return "pending", due_date

def build_alert_for_invoice(invoice: Invoice) -> dict | None:
    if invoice.internal_status == "validated":
        return None
    if invoice.internal_status == "rejected":
        return {"alert_type": "invoice_rejected", "severity": "high", "title": f"Factura {invoice.invoice_number} a fost respinsă", "message": invoice.plain_explanation or invoice.anaf_message or "Factura a fost respinsă și trebuie verificată."}
    if invoice.internal_status == "overdue":
        return {"alert_type": "invoice_overdue", "severity": "high", "title": f"Factura {invoice.invoice_number} a depășit termenul", "message": "Factura nu apare ca validată înainte de termenul calculat. Verifică urgent statusul."}
    if invoice.internal_status == "near_deadline":
        return {"alert_type": "invoice_near_deadline", "severity": "medium", "title": f"Factura {invoice.invoice_number} este aproape de termen", "message": "Factura este aproape de termenul-limită și nu este validată încă."}
    if invoice.internal_status == "unsent":
        return {"alert_type": "invoice_unsent", "severity": "medium", "title": f"Factura {invoice.invoice_number} pare netrimisă", "message": "Factura este emisă/importată, dar nu există status de transmitere/validare."}
    if invoice.anaf_message:
        return {"alert_type": "anaf_message", "severity": "low", "title": f"Factura {invoice.invoice_number} are mesaj ANAF", "message": invoice.plain_explanation or invoice.anaf_message}
    return None

def create_alert_for_invoice(db: Session, organization: Organization, invoice: Invoice, notify_email: str | None = None) -> Alert | None:
    payload = build_alert_for_invoice(invoice)
    if not payload:
        return None
    existing = db.query(Alert).filter(Alert.organization_id == organization.id, Alert.invoice_id == invoice.id, Alert.alert_type == payload["alert_type"], Alert.status == "open").first()
    if existing:
        return existing
    alert = Alert(organization_id=organization.id, invoice_id=invoice.id, alert_type=payload["alert_type"], severity=payload["severity"], title=payload["title"], message=payload["message"])
    db.add(alert)
    db.flush()
    if notify_email:
        try:
            notification_settings = get_or_create_notification_settings(db, organization, default_email=notify_email)
            recipient = get_alert_recipient(notification_settings, notify_email)
            if recipient and should_send_alert_email(notification_settings, alert.alert_type):
                send_email_notification(recipient, f"FacturaGuard: {alert.title}", f"{organization.name}\n\n{alert.message}")
                alert.sent_email = True
        except Exception as exc:
            print(f"Nu am putut trimite emailul: {exc}")
    return alert

def build_monthly_report(organization_id: int, year: int, month: int, invoices: list[Invoice]) -> dict:
    monthly = [i for i in invoices if i.issue_date.year == year and i.issue_date.month == month]
    errors = [i.plain_explanation or i.anaf_message for i in monthly if i.plain_explanation or i.anaf_message]
    top_errors = [{"error": e, "count": c} for e, c in Counter(errors).most_common(5)]
    rejected = sum(1 for i in monthly if i.internal_status == "rejected")
    overdue = sum(1 for i in monthly if i.internal_status == "overdue")
    near = sum(1 for i in monthly if i.internal_status == "near_deadline")
    unsent = sum(1 for i in monthly if i.internal_status == "unsent")
    recommendations = []
    if rejected:
        recommendations.append("Verifică datele clienților și formatul XML pentru facturile respinse.")
    if overdue:
        recommendations.append("Activează o verificare zilnică pentru facturile care se apropie de termen.")
    if near or unsent:
        recommendations.append("Stabilește un flux intern prin care facturile emise sunt verificate în aceeași zi.")
    if not recommendations:
        recommendations.append("Situația este bună. Continuă monitorizarea lunară.")
    return {"organization_id": organization_id, "year": year, "month": month, "total_invoices": len(monthly), "validated": sum(1 for i in monthly if i.internal_status == "validated"), "rejected": rejected, "unsent": unsent, "near_deadline": near, "overdue": overdue, "total_amount": round(sum(i.total_amount for i in monthly), 2), "top_errors": top_errors, "recommendations": recommendations}
