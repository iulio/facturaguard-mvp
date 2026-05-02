from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session

from .auth import hash_password, verify_password
from .models import PasswordResetToken, User
from .notifier import send_email_notification

def create_password_reset_token(db: Session, user: User) -> PasswordResetToken:
    token = PasswordResetToken(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        status="active",
        expires_at=datetime.utcnow() + timedelta(hours=2),
    )
    db.add(token)
    db.flush()

    reset_url = f"http://localhost:3000/reset-password?token={token.token}"
    send_email_notification(
        user.email,
        "FacturaGuard - resetare parolă",
        (
            "Ai cerut resetarea parolei pentru contul tău FacturaGuard.\n\n"
            f"Resetează parola aici: {reset_url}\n\n"
            "Linkul expiră în 2 ore. Dacă nu ai cerut asta, poți ignora mesajul."
        ),
    )

    return token

def reset_password_with_token(db: Session, token_value: str, new_password: str) -> User:
    token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == token_value)
        .first()
    )

    if not token:
        raise ValueError("Token invalid.")

    if token.status != "active":
        raise ValueError("Tokenul nu mai este activ.")

    if token.expires_at < datetime.utcnow():
        token.status = "expired"
        db.flush()
        raise ValueError("Tokenul a expirat.")

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        raise ValueError("Utilizatorul nu mai există.")

    user.password_hash = hash_password(new_password)
    token.status = "used"
    token.used_at = datetime.utcnow()
    db.flush()

    return user

def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise PermissionError("Parola curentă este incorectă.")

    user.password_hash = hash_password(new_password)
    db.flush()
