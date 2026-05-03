from __future__ import annotations

from dataclasses import dataclass
import io
import re
import zipfile
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Invoice, Organization, OrganizationDocument, User
from .services import compute_internal_status, create_alert_for_invoice, explain_anaf_error

@dataclass
class ParsedAnafFile:
    filename: str
    size_bytes: int
    kind: str
    status: str | None
    message: str | None
    preview: str | None

def normalize_status_from_text(text: str | None) -> str | None:
    value = (text or "").lower()

    rejected_markers = [
        "nok",
        "eroare",
        "error",
        "respins",
        "rejected",
        "invalid",
        "nu este valid",
        "nevalid",
    ]
    validated_markers = [
        "ok",
        "validat",
        "validated",
        "success",
        "preluat",
        "fără erori",
        "fara erori",
    ]

    if any(marker in value for marker in rejected_markers):
        return "rejected"

    if any(marker in value for marker in validated_markers):
        return "validated"

    if "in prelucrare" in value or "în prelucrare" in value or "pending" in value:
        return "pending"

    return None

def strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()

def parse_xml_content(filename: str, content: bytes) -> ParsedAnafFile:
    text = content.decode("utf-8", errors="replace")
    status = normalize_status_from_text(text)
    message_parts: list[str] = []

    try:
        root = ET.fromstring(content)
        for element in root.iter():
            tag = strip_namespace(element.tag)
            node_text = (element.text or "").strip()

            if not node_text:
                continue

            if any(key in tag for key in ["stare", "status", "rezultat"]):
                status = normalize_status_from_text(node_text) or status
                message_parts.append(f"{tag}: {node_text}")

            if any(key in tag for key in ["eroare", "error", "mesaj", "message", "detalii"]):
                message_parts.append(f"{tag}: {node_text}")
                status = normalize_status_from_text(node_text) or status

        if not message_parts:
            for element in list(root.iter())[:12]:
                node_text = (element.text or "").strip()
                if node_text:
                    message_parts.append(node_text)

    except Exception:
        regex_candidates = re.findall(
            r"(eroare|error|stare|status|mesaj)\s*[=:]\s*([^<\n\r]+)",
            text,
            flags=re.IGNORECASE,
        )
        for key, value in regex_candidates[:10]:
            message_parts.append(f"{key}: {value.strip()}")

    message = " | ".join(message_parts[:10])[:2000] if message_parts else text[:1000]

    return ParsedAnafFile(
        filename=filename,
        size_bytes=len(content),
        kind="xml",
        status=status,
        message=message,
        preview=text[:2000],
    )

def parse_text_content(filename: str, content: bytes) -> ParsedAnafFile:
    text = content.decode("utf-8", errors="replace")
    return ParsedAnafFile(
        filename=filename,
        size_bytes=len(content),
        kind="text",
        status=normalize_status_from_text(text),
        message=text[:2000],
        preview=text[:2000],
    )

def parse_binary_content(filename: str, content: bytes) -> ParsedAnafFile:
    return ParsedAnafFile(
        filename=filename,
        size_bytes=len(content),
        kind="binary",
        status=None,
        message=None,
        preview=None,
    )

def parse_anaf_response_zip(content: bytes) -> dict:
    files: list[ParsedAnafFile] = []

    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue

                file_content = archive.read(info.filename)
                lower_name = info.filename.lower()

                if lower_name.endswith(".xml"):
                    parsed = parse_xml_content(info.filename, file_content)
                elif lower_name.endswith((".txt", ".json", ".csv", ".log")):
                    parsed = parse_text_content(info.filename, file_content)
                else:
                    parsed = parse_binary_content(info.filename, file_content)

                files.append(parsed)
    except zipfile.BadZipFile:
        # ANAF should return ZIP, but for debugging allow raw XML/text responses.
        if content.lstrip().startswith(b"<"):
            files.append(parse_xml_content("raw-response.xml", content))
        else:
            files.append(parse_text_content("raw-response.txt", content))

    statuses = [file.status for file in files if file.status]
    if "rejected" in statuses:
        summary_status = "rejected"
    elif "validated" in statuses:
        summary_status = "validated"
    elif "pending" in statuses:
        summary_status = "pending"
    else:
        summary_status = "unknown"

    messages = [file.message for file in files if file.message]
    summary_message = " | ".join(messages[:5])[:3000] if messages else "Nu au fost extrase mesaje din răspunsul ANAF."

    return {
        "file_count": len(files),
        "xml_file_count": sum(1 for file in files if file.kind == "xml"),
        "summary_status": summary_status,
        "summary_message": summary_message,
        "files": [
            {
                "filename": file.filename,
                "size_bytes": file.size_bytes,
                "kind": file.kind,
                "status": file.status,
                "message": file.message,
                "preview": file.preview,
            }
            for file in files
        ],
    }

def parse_and_apply_anaf_response(
    db: Session,
    organization: Organization,
    invoice: Invoice,
    document: OrganizationDocument,
    content: bytes,
    actor: User,
    apply_result: bool = True,
) -> dict:
    parsed = parse_anaf_response_zip(content)

    if apply_result and parsed["summary_status"] in {"validated", "rejected", "pending"}:
        invoice.anaf_status = parsed["summary_status"]
        invoice.anaf_message = parsed["summary_message"]
        invoice.plain_explanation = explain_anaf_error(parsed["summary_message"])
        internal_status, _ = compute_internal_status(invoice.issue_date, parsed["summary_status"])
        invoice.internal_status = internal_status

        if internal_status in {"rejected", "overdue", "near_deadline", "unsent"}:
            create_alert_for_invoice(db, organization, invoice, notify_email=None)

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="anaf.response_parsed",
        entity_type="organization_document",
        entity_id=document.id,
        message=f"Răspuns ANAF parsabil analizat pentru factura {invoice.invoice_number}: {parsed['summary_status']}.",
    )

    db.flush()

    return parsed
