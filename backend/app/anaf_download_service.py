from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .access import write_audit_log
from .anaf_client import RealAnafClient
from .anaf_oauth_service import get_anaf_api_base, get_valid_access_token
from .file_storage import store_upload_file
from .models import Invoice, Organization, User
from .settings import get_settings

@dataclass
class SyntheticUploadFile:
    filename: str
    content_type: str = "application/zip"

def build_anaf_response_filename(invoice: Invoice, download_id: str) -> str:
    safe_number = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in invoice.invoice_number)
    safe_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in download_id)
    return f"anaf-response-{safe_number}-{safe_id}.zip"

def download_anaf_response_zip(
    db: Session,
    organization: Organization,
    invoice: Invoice,
    actor: User,
    message_id: str | None = None,
) -> dict:
    settings = get_settings()

    download_id = message_id or invoice.anaf_download_id

    if settings.anaf_connector_mode != "real":
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "downloaded": False,
            "anaf_download_id": download_id,
            "document_id": invoice.anaf_response_document_id,
            "filename": None,
            "message": "ANAF_CONNECTOR_MODE nu este real. Setează ANAF_CONNECTOR_MODE=real pentru descărcare.",
            "size_bytes": None,
        }

    if not download_id:
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "downloaded": False,
            "anaf_download_id": None,
            "document_id": invoice.anaf_response_document_id,
            "filename": None,
            "message": "Factura nu are anaf_download_id. Rulează stareMesaj sau introdu un message_id.",
            "size_bytes": None,
        }

    try:
        access_token = get_valid_access_token(db, organization.id)
    except RuntimeError as exc:
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "downloaded": False,
            "anaf_download_id": download_id,
            "document_id": invoice.anaf_response_document_id,
            "filename": None,
            "message": str(exc),
            "size_bytes": None,
        }

    client = RealAnafClient(
        access_token=access_token,
        base_url=get_anaf_api_base(),
    )

    try:
        content = client.download_message(download_id)
    except Exception as exc:
        write_audit_log(
            db,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action="anaf.response_download_failed",
            entity_type="invoice",
            entity_id=invoice.id,
            message=f"Descărcare răspuns ANAF eșuată pentru factura {invoice.invoice_number}: {exc}",
        )
        db.flush()
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": True,
            "downloaded": False,
            "anaf_download_id": download_id,
            "document_id": invoice.anaf_response_document_id,
            "filename": None,
            "message": f"Descărcare răspuns ANAF eșuată: {exc}",
            "size_bytes": None,
        }

    filename = build_anaf_response_filename(invoice, download_id)
    synthetic_file = SyntheticUploadFile(filename=filename)

    document = store_upload_file(
        db,
        organization=organization,
        upload_file=synthetic_file,
        content=content,
        actor=actor,
        document_type="anaf_response",
    )

    invoice.anaf_download_id = download_id
    invoice.anaf_response_document_id = document.id
    invoice.anaf_submission_environment = settings.anaf_env

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="anaf.response_downloaded",
        entity_type="organization_document",
        entity_id=document.id,
        message=f"Răspuns ANAF descărcat și stocat pentru factura {invoice.invoice_number}.",
    )

    db.flush()

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "environment": settings.anaf_env,
        "attempted": True,
        "downloaded": True,
        "anaf_download_id": download_id,
        "document_id": document.id,
        "filename": filename,
        "message": "Răspuns ANAF descărcat și salvat în document storage.",
        "size_bytes": len(content),
    }
