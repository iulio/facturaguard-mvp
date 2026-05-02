import os, smtplib
from email.message import EmailMessage

def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    dry_run = os.getenv("FG_EMAIL_DRY_RUN", "true").lower() != "false"
    if dry_run:
        print("\n--- FacturaGuard email dry-run ---")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(body)
        print("--- end email ---\n")
        return True

    host = os.getenv("FG_SMTP_HOST")
    port = int(os.getenv("FG_SMTP_PORT", "587"))
    user = os.getenv("FG_SMTP_USERNAME")
    password = os.getenv("FG_SMTP_PASSWORD")
    sender = os.getenv("FG_EMAIL_FROM", user or "alerts@facturaguard.local")
    if not host or not user or not password:
        raise RuntimeError("SMTP nu este configurat complet.")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
    return True
