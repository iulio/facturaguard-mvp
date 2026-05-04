from __future__ import annotations

from sqlalchemy.orm import Session

from .models import (
    Alert,
    AnafAuthorization,
    ApiKey,
    AuditLog,
    Invoice,
    Organization,
    OrganizationDocument,
    OrganizationIntegration,
    PaymentTransaction,
    User,
)
from .portfolio_service import get_accessible_organization_ids
from .settings import get_settings


def build_onboarding_status(db: Session, user: User) -> dict:
    """Existing user-level onboarding status used by the dashboard."""
    organization_ids = get_accessible_organization_ids(db, user)

    if not organization_ids:
        return {
            "has_organization": False,
            "organization_id": None,
            "organization_name": None,
            "has_invoices": False,
            "invoice_count": 0,
            "has_run_sync": False,
            "open_alerts": 0,
            "completed": False,
            "next_step": "create_organization",
        }

    organization = (
        db.query(Organization)
        .filter(Organization.id.in_(organization_ids))
        .order_by(Organization.created_at.asc())
        .first()
    )

    invoice_count = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization.id)
        .count()
    )

    open_alerts = (
        db.query(Alert)
        .filter(Alert.organization_id == organization.id, Alert.status == "open")
        .count()
    )

    has_run_sync = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == organization.id,
            AuditLog.action.in_([
                "invoice.status_synced",
                "organization.status_sync_completed",
                "anaf.connection_tested",
            ]),
        )
        .count()
        > 0
    )

    if invoice_count == 0:
        next_step = "upload_invoices"
    elif not has_run_sync:
        next_step = "run_sync"
    else:
        next_step = "review_dashboard"

    completed = invoice_count > 0 and has_run_sync

    return {
        "has_organization": True,
        "organization_id": organization.id,
        "organization_name": organization.name,
        "has_invoices": invoice_count > 0,
        "invoice_count": invoice_count,
        "has_run_sync": has_run_sync,
        "open_alerts": open_alerts,
        "completed": completed,
        "next_step": next_step,
    }


def _step(
    key: str,
    title: str,
    description: str,
    done: bool,
    href: str,
    category: str,
    priority: int,
) -> dict:
    return {
        "key": key,
        "title": title,
        "description": description,
        "done": done,
        "href": href,
        "category": category,
        "priority": priority,
    }


def build_onboarding_checklist(db: Session, organization: Organization) -> dict:
    """Organization-level checklist for pilot/deployment setup."""
    settings = get_settings()

    invoice_count = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization.id)
        .count()
    )
    document_count = (
        db.query(OrganizationDocument)
        .filter(OrganizationDocument.organization_id == organization.id)
        .count()
    )
    api_key_count = (
        db.query(ApiKey)
        .filter(ApiKey.organization_id == organization.id, ApiKey.status == "active")
        .count()
    )
    payment_count = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.organization_id == organization.id)
        .count()
    )
    integration = (
        db.query(OrganizationIntegration)
        .filter(OrganizationIntegration.organization_id == organization.id, OrganizationIntegration.provider == "anaf")
        .first()
    )
    anaf_auth_count = (
        db.query(AnafAuthorization)
        .filter(AnafAuthorization.organization_id == organization.id, AnafAuthorization.status == "active")
        .count()
    )

    anaf_ready = settings.anaf_connector_mode == "real" and anaf_auth_count > 0
    netopia_ready = settings.netopia_provider == "v2"

    steps = [
        _step(
            "organization_created",
            "Creează firma",
            "Firma activă există în cont și poate primi importuri.",
            True,
            "/",
            "core",
            1,
        ),
        _step(
            "import_invoices",
            "Importă primele facturi",
            "Încarcă un CSV/XML de test ca să verifici dashboardul, alertele și rapoartele.",
            invoice_count > 0,
            "/templates",
            "core",
            2,
        ),
        _step(
            "documents_storage",
            "Verifică document storage",
            "Încarcă sau generează cel puțin un document fiscal, raport sau răspuns ANAF.",
            document_count > 0,
            "/documents",
            "core",
            3,
        ),
        _step(
            "deployment_readiness",
            "Rulează deployment readiness",
            "Verifică setările runtime pentru DB, storage, CORS, ANAF și NETOPIA.",
            False,
            "/deployment",
            "deployment",
            4,
        ),
        _step(
            "public_status",
            "Verifică pagina publică de status",
            "Confirmă că /status funcționează fără autentificare după deploy.",
            False,
            "/status",
            "deployment",
            5,
        ),
        _step(
            "billing_configured",
            "Configurează billing",
            "Pornește cu NETOPIA mock, apoi treci pe sandbox v2 când ai credentialele.",
            payment_count > 0 or netopia_ready,
            "/billing",
            "payments",
            6,
        ),
        _step(
            "anaf_configured",
            "Configurează ANAF/SPV",
            "Începe cu mock, apoi conectează OAuth real în mediul de test.",
            bool(integration and integration.status in {"connected", "ok"}) or anaf_ready,
            "/integrations",
            "anaf",
            7,
        ),
        _step(
            "ubl_xml",
            "Generează XML UBL",
            "Alege o factură și generează XML-ul UBL skeleton pentru validare.",
            False,
            "/ubl",
            "anaf",
            8,
        ),
        _step(
            "api_key",
            "Creează o cheie API",
            "Generează o cheie API pentru integrare cu sisteme externe.",
            api_key_count > 0,
            "/api-keys",
            "developer",
            9,
        ),
    ]

    done = sum(1 for step in steps if step["done"])
    total = len(steps)
    percent = round((done / total) * 100) if total else 0

    blockers = [step for step in steps if not step["done"] and step["priority"] <= 3]
    next_step = next((step for step in steps if not step["done"]), None)

    return {
        "organization_id": organization.id,
        "organization_name": organization.name,
        "progress": {
            "done": done,
            "total": total,
            "percent": percent,
        },
        "next_step": next_step,
        "blockers": blockers,
        "steps": sorted(steps, key=lambda item: item["priority"]),
        "context": {
            "invoice_count": invoice_count,
            "document_count": document_count,
            "api_key_count": api_key_count,
            "payment_count": payment_count,
            "anaf_connector_mode": settings.anaf_connector_mode,
            "netopia_provider": settings.netopia_provider,
        },
    }
