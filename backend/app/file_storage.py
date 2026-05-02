from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Organization, OrganizationDocument, User
from .settings import get_settings

def get_organization_storage_dir(organization_id: int) -> Path:
    settings = get_settings()
    path = Path(settings.file_storage_path) / "organizations" / str(organization_id)
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_suffix(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if len(suffix) > 20:
        return ""
    return suffix

def store_upload_file(
    db: Session,
    organization: Organization,
    upload_file: UploadFile,
    content: bytes,
    actor: User | None = None,
    document_type: str = "invoice_import",
) -> OrganizationDocument:
    storage_dir = get_organization_storage_dir(organization.id)
    stored_filename = f"{uuid.uuid4().hex}{safe_suffix(upload_file.filename or '')}"
    storage_path = storage_dir / stored_filename

    with open(storage_path, "wb") as f:
        f.write(content)

    document = OrganizationDocument(
        organization_id=organization.id,
        uploaded_by_user_id=actor.id if actor else None,
        original_filename=upload_file.filename or stored_filename,
        stored_filename=stored_filename,
        storage_path=str(storage_path),
        content_type=upload_file.content_type,
        file_size=len(content),
        document_type=document_type,
        status="stored",
    )

    db.add(document)
    db.flush()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id if actor else None,
        action="document.stored",
        entity_type="organization_document",
        entity_id=document.id,
        message=f"Documentul {document.original_filename} a fost stocat pentru audit.",
    )

    return document

def resolve_document_path(document: OrganizationDocument) -> Path:
    path = Path(document.storage_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Fișierul nu mai există în storage.")
    return path
