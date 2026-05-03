from __future__ import annotations

import re
from datetime import datetime
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from .access import write_audit_log
from .anaf_client import RealAnafClient
from .anaf_oauth_service import get_anaf_api_base, get_valid_access_token
from .models import Invoice, Organization, User
from .services import compute_internal_status, create_alert_for_invoice, explain_anaf_error
from .settings import get_settings

def normalize_anaf_status(raw_status: str | None, raw_message: str | None = None) -> str:
    value = (raw_status or "").lower()
    message = (raw_message or "").lower()

    rejected_markers = ["nok", "eroare", "error", "respins", "rejected", "invalid"]
    validated_markers = ["ok", "validat", "validated", "success", "preluat"]

    if any(marker in value or marker in message for marker in rejected_markers):
        return "rejected"

    if any(marker in value for marker in validated_markers):
        return "validated"

    if any(marker in message for marker in validated_markers) and not any(marker in message for marker in rejected_markers):
        return "validated"

    return "pending"

def parse_anaf_status_response(raw_response: str) -> dict:
    """Best-effort parser for ANAF stareMesaj response.

    This parser intentionally accepts multiple XML or text-like response shapes.
    The raw response is kept in `raw_response` for audit/debugging.
    """
    result = {
        "status": "pending",
        "message": raw_response[:1000] if raw_response else "",
        "download_id": None,
    }

    if not raw_response:
        result["message"] = "Răspuns ANAF gol."
        return result

    try:
        root = ET.fromstring(raw_response.encode("utf-8"))
        collected_text = []
        for element in root.iter():
            tag = element.tag.lower()
            text = (element.text or "").strip()
            if text:
                collected_text.append(text)

            if text and any(key in tag for key in ["stare", "status", "statusprelucrare"]):
                result["status"] = normalize_anaf_status(text, raw_response)

            if text and any(key in tag for key in ["mesaj", "message", "eroare", "error"]):
                result["message"] = text

            if text and any(key in tag for key in ["iddescarcare", "id_descarcare", "downloadid"]):
                result["download_id"] = text

            for attr_name, attr_value in element.attrib.items():
                attr = attr_name.lower()
                if attr_value and any(key in attr for key in ["stare", "status"]):
                    result["status"] = normalize_anaf_status(attr_value, raw_response)
                if attr_value and any(key in attr for key in ["iddescarcare", "id_descarcare", "downloadid"]):
                    result["download_id"] = attr_value

        if result["message"] == raw_response[:1000] and collected_text:
            result["message"] = " | ".join(collected_text[:5])[:1000]

        result["status"] = normalize_anaf_status(result["status"], result["message"])
        return result
    except Exception:
        pass

    status_patterns = [
        r"stare[=:\s\"]+([A-Za-z0-9_-]+)",
        r"status[=:\s\"]+([A-Za-z0-9_-]+)",
    ]
    for pattern in status_patterns:
        match = re.search(pattern, raw_response, flags=re.IGNORECASE)
        if match:
            result["status"] = normalize_anaf_status(match.group(1), raw_response)
            break

    download_match = re.search(
        r"(id_descarcare|idDescarcare|downloadId)[=:\s\"]+(\d+)",
        raw_response,
        flags=re.IGNORECASE,
    )
    if download_match:
        result["download_id"] = download_match.group(2)

    result["status"] = normalize_anaf_status(result["status"], raw_response)
    return result

def check_invoice_status_from_anaf(
    db: Session,
    organization: Organization,
    invoice: Invoice,
    actor: User,
) -> dict:
    settings = get_settings()

    if settings.anaf_connector_mode != "real":
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "checked": False,
            "anaf_upload_id": invoice.anaf_upload_id,
            "anaf_status": invoice.anaf_status,
            "internal_status": invoice.internal_status,
            "message": "ANAF_CONNECTOR_MODE nu este real. Setează ANAF_CONNECTOR_MODE=real pentru stareMesaj.",
            "raw_response": None,
        }

    if not invoice.anaf_upload_id:
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "checked": False,
            "anaf_upload_id": None,
            "anaf_status": invoice.anaf_status,
            "internal_status": invoice.internal_status,
            "message": "Factura nu are anaf_upload_id/id_incarcare. Fă upload înainte de verificarea statusului.",
            "raw_response": None,
        }

    try:
        access_token = get_valid_access_token(db, organization.id)
    except RuntimeError as exc:
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "checked": False,
            "anaf_upload_id": invoice.anaf_upload_id,
            "anaf_status": invoice.anaf_status,
            "internal_status": invoice.internal_status,
            "message": str(exc),
            "raw_response": None,
        }

    client = RealAnafClient(
        access_token=access_token,
        base_url=get_anaf_api_base(),
    )

    try:
        status_result = client.fetch_invoice_status(invoice)
        raw_response = status_result.message or ""
        parsed = parse_anaf_status_response(raw_response)
    except Exception as exc:
        write_audit_log(
            db,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action="anaf.status_check_failed",
            entity_type="invoice",
            entity_id=invoice.id,
            message=f"Verificare stareMesaj eșuată pentru factura {invoice.invoice_number}: {exc}",
        )
        db.flush()
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": True,
            "checked": False,
            "anaf_upload_id": invoice.anaf_upload_id,
            "anaf_status": invoice.anaf_status,
            "internal_status": invoice.internal_status,
            "message": f"Verificare stareMesaj eșuată: {exc}",
            "raw_response": None,
        }

    invoice.anaf_status = parsed["status"]
    invoice.anaf_message = parsed["message"]
    invoice.plain_explanation = explain_anaf_error(parsed["message"])
    if parsed.get("download_id"):
        invoice.anaf_download_id = parsed.get("download_id")
    invoice.anaf_last_checked_at = datetime.utcnow()
    invoice.anaf_submission_environment = settings.anaf_env
    internal_status, _ = compute_internal_status(invoice.issue_date, parsed["status"])
    invoice.internal_status = internal_status

    if internal_status in {"rejected", "overdue", "near_deadline", "unsent"}:
        create_alert_for_invoice(db, organization, invoice, notify_email=None)

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="anaf.status_checked",
        entity_type="invoice",
        entity_id=invoice.id,
        message=f"stareMesaj verificat pentru factura {invoice.invoice_number}: {parsed['status']}.",
    )

    db.flush()

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "environment": settings.anaf_env,
        "attempted": True,
        "checked": True,
        "anaf_upload_id": invoice.anaf_upload_id,
        "anaf_status": invoice.anaf_status,
        "internal_status": invoice.internal_status,
        "message": parsed["message"],
        "raw_response": raw_response[:5000],
    }
