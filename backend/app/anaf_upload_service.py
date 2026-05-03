from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from .access import write_audit_log
from .anaf_client import RealAnafClient
from .anaf_oauth_service import get_anaf_api_base, get_valid_access_token
from .models import Invoice, Organization, User
from .settings import get_settings
from .ubl_generator import build_basic_ubl_invoice_xml

def extract_upload_id(raw_response: str) -> str | None:
    """Best-effort parser for ANAF upload response.

    Real ANAF responses may vary by endpoint/version. This parser intentionally
    accepts several common shapes and falls back to regex.
    """
    if not raw_response:
        return None

    try:
        root = ET.fromstring(raw_response.encode("utf-8"))
        for element in root.iter():
            tag = element.tag.lower()
            text = (element.text or "").strip()
            if text and any(key in tag for key in ["id_incarcare", "idincarcare", "uploadid"]):
                return text

            for attr_name, attr_value in element.attrib.items():
                attr = attr_name.lower()
                if attr_value and any(key in attr for key in ["id_incarcare", "idincarcare", "uploadid"]):
                    return attr_value
    except Exception:
        pass

    patterns = [
        r"id_incarcare[=:\s\"]+(\d+)",
        r"idIncarcare[=:\s\"]+(\d+)",
        r"uploadId[=:\s\"]+(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_response, flags=re.IGNORECASE)
        if match:
            return match.group(1)

    return None

def upload_invoice_xml_to_anaf(
    db: Session,
    organization: Organization,
    invoice: Invoice,
    actor: User,
    dry_run: bool = False,
) -> dict:
    settings = get_settings()

    if settings.anaf_connector_mode != "real":
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "uploaded": False,
            "anaf_upload_id": invoice.anaf_upload_id,
            "message": "ANAF_CONNECTOR_MODE nu este real. Setează ANAF_CONNECTOR_MODE=real pentru upload.",
            "raw_response": None,
        }

    xml = build_basic_ubl_invoice_xml(invoice, organization)

    if dry_run:
        write_audit_log(
            db,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action="anaf.upload_dry_run",
            entity_type="invoice",
            entity_id=invoice.id,
            message=f"Dry-run upload ANAF pentru factura {invoice.invoice_number}.",
        )
        db.flush()
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "uploaded": False,
            "anaf_upload_id": invoice.anaf_upload_id,
            "message": "Dry-run: XML generat, dar nu a fost trimis către ANAF.",
            "raw_response": xml[:2000],
        }

    try:
        access_token = get_valid_access_token(db, organization.id)
    except RuntimeError as exc:
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": False,
            "uploaded": False,
            "anaf_upload_id": invoice.anaf_upload_id,
            "message": str(exc),
            "raw_response": None,
        }

    client = RealAnafClient(
        access_token=access_token,
        base_url=get_anaf_api_base(),
    )

    try:
        raw_response = client.upload_invoice_xml(
            xml_bytes=xml.encode("utf-8"),
            cif=organization.cui,
            standard="UBL",
        )
    except Exception as exc:
        write_audit_log(
            db,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action="anaf.upload_failed",
            entity_type="invoice",
            entity_id=invoice.id,
            message=f"Upload ANAF eșuat pentru factura {invoice.invoice_number}: {exc}",
        )
        db.flush()
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "environment": settings.anaf_env,
            "attempted": True,
            "uploaded": False,
            "anaf_upload_id": invoice.anaf_upload_id,
            "message": f"Upload ANAF eșuat: {exc}",
            "raw_response": None,
        }

    upload_id = extract_upload_id(raw_response)

    invoice.anaf_upload_id = upload_id or invoice.anaf_upload_id
    invoice.anaf_status = "uploaded" if upload_id else "pending"
    invoice.anaf_submission_environment = settings.anaf_env
    invoice.internal_status = "pending"

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="anaf.upload_submitted",
        entity_type="invoice",
        entity_id=invoice.id,
        message=f"Factura {invoice.invoice_number} a fost trimisă către ANAF. id_incarcare={upload_id or 'necunoscut'}.",
    )

    db.flush()

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "environment": settings.anaf_env,
        "attempted": True,
        "uploaded": bool(upload_id),
        "anaf_upload_id": upload_id,
        "message": "Upload ANAF trimis. Verifică statusul prin stareMesaj." if upload_id else "Upload trimis, dar id_incarcare nu a putut fi extras automat.",
        "raw_response": raw_response[:5000],
    }
