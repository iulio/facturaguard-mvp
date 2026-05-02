from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Organization, OrganizationDocument, User
from .settings import get_settings

@dataclass
class StoredObject:
    storage_path: str
    stored_filename: str
    size: int

class StorageBackend(ABC):
    @abstractmethod
    def save(self, organization_id: int, original_filename: str, content: bytes) -> StoredObject:
        raise NotImplementedError

    @abstractmethod
    def read(self, storage_path: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        raise NotImplementedError

class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _organization_dir(self, organization_id: int) -> Path:
        path = self.base_path / "organizations" / str(organization_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(self, organization_id: int, original_filename: str, content: bytes) -> StoredObject:
        suffix = safe_suffix(original_filename)
        stored_filename = f"{uuid.uuid4().hex}{suffix}"
        path = self._organization_dir(organization_id) / stored_filename

        with open(path, "wb") as f:
            f.write(content)

        return StoredObject(
            storage_path=str(path),
            stored_filename=stored_filename,
            size=len(content),
        )

    def read(self, storage_path: str) -> bytes:
        path = Path(storage_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError("Fișierul nu mai există în storage.")
        return path.read_bytes()

    def exists(self, storage_path: str) -> bool:
        path = Path(storage_path)
        return path.exists() and path.is_file()

class S3StorageBackend(StorageBackend):
    def __init__(self):
        settings = get_settings()

        if not settings.s3_bucket_name:
            raise RuntimeError("S3_BUCKET_NAME este obligatoriu pentru storage S3.")

        import boto3

        self.bucket_name = settings.s3_bucket_name
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region_name,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )

    def save(self, organization_id: int, original_filename: str, content: bytes) -> StoredObject:
        suffix = safe_suffix(original_filename)
        stored_filename = f"{uuid.uuid4().hex}{suffix}"
        key = f"organizations/{organization_id}/{stored_filename}"

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
        )

        return StoredObject(
            storage_path=f"s3://{self.bucket_name}/{key}",
            stored_filename=stored_filename,
            size=len(content),
        )

    def read(self, storage_path: str) -> bytes:
        bucket, key = parse_s3_uri(storage_path)
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def exists(self, storage_path: str) -> bool:
        bucket, key = parse_s3_uri(storage_path)
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

def parse_s3_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError("Invalid S3 URI.")
    without_scheme = uri[5:]
    bucket, _, key = without_scheme.partition("/")
    if not bucket or not key:
        raise ValueError("Invalid S3 URI.")
    return bucket, key

def safe_suffix(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if len(suffix) > 20:
        return ""
    return suffix

def get_storage_backend() -> StorageBackend:
    settings = get_settings()

    if settings.file_storage_backend.lower() == "s3":
        return S3StorageBackend()

    return LocalStorageBackend(settings.file_storage_path)

def store_upload_file(
    db: Session,
    organization: Organization,
    upload_file: UploadFile,
    content: bytes,
    actor: User | None = None,
    document_type: str = "invoice_import",
) -> OrganizationDocument:
    backend = get_storage_backend()
    stored = backend.save(organization.id, upload_file.filename or "upload.bin", content)

    document = OrganizationDocument(
        organization_id=organization.id,
        uploaded_by_user_id=actor.id if actor else None,
        original_filename=upload_file.filename or stored.stored_filename,
        stored_filename=stored.stored_filename,
        storage_path=stored.storage_path,
        content_type=upload_file.content_type,
        file_size=stored.size,
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

def read_document_content(document: OrganizationDocument) -> bytes:
    backend = get_storage_backend()
    if not backend.exists(document.storage_path):
        raise FileNotFoundError("Fișierul nu mai există în storage.")
    return backend.read(document.storage_path)

# Backward-compatible alias used by older code paths.
def resolve_document_path(document: OrganizationDocument):
    return document.storage_path
