import smtplib
from email.message import EmailMessage
from .settings import get_settings

def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    settings = get_settings()

    if settings.fg_email_dry_run:
        print("\n--- FacturaGuard email dry-run ---")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(body)
        print("--- end email ---\n")
        return True

    if not settings.fg_smtp_host or not settings.fg_smtp_username or not settings.fg_smtp_password:
        raise RuntimeError("SMTP nu este configurat complet.")

    msg = EmailMessage()
    msg["From"] = settings.fg_email_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.fg_smtp_host, settings.fg_smtp_port) as server:
        server.starttls()
        server.login(settings.fg_smtp_username, settings.fg_smtp_password)
        server.send_message(msg)

    return True
