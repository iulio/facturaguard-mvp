from dataclasses import dataclass
from datetime import datetime
import hashlib
import httpx

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


class RealAnafClient(BaseAnafClient):
    """Real ANAF/SPV HTTP client skeleton.

    This class contains the HTTP methods needed for production integration.
    The OAuth token is supplied by anaf_oauth_service.get_valid_access_token().
    Existing sync flows still need to be wired to token retrieval before they
    should be used against production.
    """

    def __init__(self, access_token: str | None = None, base_url: str | None = None):
        self.access_token = access_token
        self.base_url = base_url

    def _headers(self) -> dict:
        if not self.access_token:
            raise RuntimeError("Access token ANAF lipsă.")
        return {"Authorization": f"Bearer {self.access_token}"}

    def test_connection(self) -> tuple[str, str]:
        if not self.access_token:
            return "pending_oauth", "Conectorul ANAF real este configurat, dar lipsește tokenul OAuth."
        return "configured", "Conectorul ANAF real are access token disponibil."

    def fetch_invoice_status(self, invoice: Invoice) -> AnafStatusResult:
        if not invoice.anaf_upload_id:
            return AnafStatusResult(
                status=invoice.anaf_status or "pending",
                message="Factura nu are încă id_incarcare ANAF.",
                upload_id=None,
            )

        if not self.base_url:
            return AnafStatusResult(
                status=invoice.anaf_status or "pending",
                message="Real ANAF client nu are base_url configurat.",
                upload_id=invoice.anaf_upload_id,
            )

        response = httpx.get(
            f"{self.base_url}/stareMesaj",
            params={"id_incarcare": invoice.anaf_upload_id},
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()

        # Skeleton parser: păstrăm statusul existent până adăugăm parser XML complet.
        return AnafStatusResult(
            status=invoice.anaf_status or "pending",
            message=response.text[:1000],
            upload_id=invoice.anaf_upload_id,
        )

    def upload_invoice_xml(self, xml_bytes: bytes, cif: str, standard: str = "UBL") -> str:
        if not self.base_url:
            raise RuntimeError("Real ANAF client nu are base_url configurat.")

        response = httpx.post(
            f"{self.base_url}/upload",
            params={"standard": standard, "cif": cif.replace("RO", "").strip()},
            headers={**self._headers(), "Content-Type": "application/xml"},
            content=xml_bytes,
            timeout=60,
        )
        response.raise_for_status()
        return response.text

    def list_messages(self, cif: str, days: int = 10) -> str:
        if not self.base_url:
            raise RuntimeError("Real ANAF client nu are base_url configurat.")

        response = httpx.get(
            f"{self.base_url}/listaMesajeFactura",
            params={"zile": days, "cif": cif.replace("RO", "").strip()},
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.text

    def download_message(self, message_id: str) -> bytes:
        if not self.base_url:
            raise RuntimeError("Real ANAF client nu are base_url configurat.")

        response = httpx.get(
            f"{self.base_url}/descarcare",
            params={"id": message_id},
            headers=self._headers(),
            timeout=60,
        )
        response.raise_for_status()
        return response.content


def get_anaf_client(integration: OrganizationIntegration | None = None) -> BaseAnafClient:
    if integration and integration.mode == "real":
        return RealAnafClient()
    return MockAnafClient()
