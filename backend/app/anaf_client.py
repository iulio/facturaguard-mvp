from dataclasses import dataclass
from datetime import datetime
import hashlib

from .models import Invoice, OrganizationIntegration

@dataclass
class AnafStatusResult:
    status: str
    message: str | None = None
    upload_id: str | None = None

class BaseAnafClient:
    def test_connection(self) -> tuple[str, str]:
        raise NotImplementedError

    def fetch_invoice_status(self, invoice: Invoice) -> AnafStatusResult:
        raise NotImplementedError

class MockAnafClient(BaseAnafClient):
    """Deterministic mock connector for local development and CI.

    This does not call ANAF. It simulates status updates so the product flow
    can be developed before the real SPV/e-Factura connector is implemented.
    """

    def test_connection(self) -> tuple[str, str]:
        return "connected", "Mock ANAF connector is available."

    def fetch_invoice_status(self, invoice: Invoice) -> AnafStatusResult:
        seed = f"{invoice.invoice_number}:{invoice.customer_cui}:{invoice.total_amount}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        bucket = int(digest[:2], 16) % 10

        if invoice.anaf_status == "rejected":
            return AnafStatusResult(
                status="rejected",
                message=invoice.anaf_message or "Factura este respinsă în mock ANAF.",
                upload_id=invoice.anaf_upload_id or f"MOCK-{digest[:10]}",
            )

        if bucket <= 5:
            return AnafStatusResult(
                status="validated",
                message=None,
                upload_id=invoice.anaf_upload_id or f"MOCK-{digest[:10]}",
            )

        if bucket <= 7:
            return AnafStatusResult(
                status="pending",
                message="Factura este încă în procesare în mock ANAF.",
                upload_id=invoice.anaf_upload_id or f"MOCK-{digest[:10]}",
            )

        return AnafStatusResult(
            status="rejected",
            message="Mock ANAF: eroare de validare XML/CUI.",
            upload_id=invoice.anaf_upload_id or f"MOCK-{digest[:10]}",
        )

def get_anaf_client(integration: OrganizationIntegration | None = None) -> BaseAnafClient:
    # Future: return a real ANAF/SPV client when integration.mode == "live".
    return MockAnafClient()
