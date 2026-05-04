from __future__ import annotations

from sqlalchemy.orm import Session

from .deployment_readiness_service import build_deployment_readiness
from .models import Invoice, Organization, OrganizationDocument, PaymentTransaction
from .onboarding_service import build_onboarding_checklist
from .settings import get_settings

def build_pilot_workspace(db: Session, organization: Organization, engine) -> dict:
    settings = get_settings()

    onboarding = build_onboarding_checklist(db, organization)
    readiness = build_deployment_readiness(engine)

    invoice_count = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization.id)
        .count()
    )
    rejected_count = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization.id, Invoice.internal_status == "rejected")
        .count()
    )
    pending_count = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization.id, Invoice.internal_status == "pending")
        .count()
    )
    document_count = (
        db.query(OrganizationDocument)
        .filter(OrganizationDocument.organization_id == organization.id)
        .count()
    )
    payment_count = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.organization_id == organization.id)
        .count()
    )

    next_actions = []

    if invoice_count == 0:
        next_actions.append({
            "title": "Importă facturile pilot",
            "description": "Încarcă un CSV/XML de test pentru firma selectată.",
            "href": "/templates",
            "priority": "high",
        })

    if readiness["overall_status"] != "pass":
        next_actions.append({
            "title": "Verifică deployment readiness",
            "description": "Rezolvă warningurile/failurile pentru Railway, DB, storage și integrări.",
            "href": "/deployment",
            "priority": "high" if readiness["overall_status"] == "fail" else "medium",
        })

    if settings.netopia_provider == "mock":
        next_actions.append({
            "title": "Pregătește NETOPIA sandbox",
            "description": "NETOPIA este încă în mock mode. Treci pe v2 sandbox după credentiale.",
            "href": "/billing",
            "priority": "medium",
        })

    if settings.anaf_connector_mode == "mock":
        next_actions.append({
            "title": "Pregătește ANAF/SPV test",
            "description": "ANAF este încă în mock mode. Configurează OAuth și ANAF_ENV=test.",
            "href": "/integrations",
            "priority": "medium",
        })

    if document_count == 0:
        next_actions.append({
            "title": "Testează document storage",
            "description": "Încarcă un document sau generează un raport pentru a valida storage-ul.",
            "href": "/documents",
            "priority": "medium",
        })

    if not next_actions:
        next_actions.append({
            "title": "Rulează smoke test post-deploy",
            "description": "Folosește scripts/railway_smoke_test.py după deploy.",
            "href": "/deployment",
            "priority": "low",
        })

    return {
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "cui": organization.cui,
        },
        "app": {
            "version": settings.app_version,
            "environment": settings.environment,
        },
        "summary": {
            "invoice_count": invoice_count,
            "pending_count": pending_count,
            "rejected_count": rejected_count,
            "document_count": document_count,
            "payment_count": payment_count,
            "onboarding_percent": onboarding["progress"]["percent"],
            "deployment_status": readiness["overall_status"],
            "anaf_mode": settings.anaf_connector_mode,
            "netopia_provider": settings.netopia_provider,
        },
        "next_actions": next_actions,
        "onboarding": onboarding,
        "readiness_summary": readiness["summary"],
        "readiness_status": readiness["overall_status"],
    }
