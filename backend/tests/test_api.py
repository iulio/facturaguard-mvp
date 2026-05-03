import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"

def register_user(prefix: str = "user"):
    email = unique_email(prefix)
    response = client.post(
        "/auth/register",
        json={"name": prefix.title(), "email": email, "password": "Password123!"},
    )
    assert response.status_code == 200, response.text
    return email, response.json()["access_token"]

def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}

def test_health_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_register_create_org_and_audit_log():
    _, token = register_user("accountant")

    org_response = client.post(
        "/organizations",
        json={"name": "Test SRL", "cui": "RO12345678"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200, org_response.text
    org = org_response.json()

    list_response = client.get("/organizations", headers=auth_header(token))
    assert list_response.status_code == 200
    assert any(item["id"] == org["id"] for item in list_response.json())

    logs_response = client.get(f"/organizations/{org['id']}/audit-logs", headers=auth_header(token))
    assert logs_response.status_code == 200
    logs = logs_response.json()
    assert any(log["action"] == "organization.created" for log in logs)

def test_member_viewer_can_read_but_not_upload():
    _, owner_token = register_user("owner")
    viewer_email, viewer_token = register_user("viewer")

    org_response = client.post(
        "/organizations",
        json={"name": "Viewer Test SRL", "cui": "RO87654321"},
        headers=auth_header(owner_token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    member_response = client.post(
        f"/organizations/{org_id}/members",
        json={"email": viewer_email, "role": "client_viewer"},
        headers=auth_header(owner_token),
    )
    assert member_response.status_code == 200, member_response.text

    dashboard_response = client.get(
        f"/organizations/{org_id}/dashboard",
        headers=auth_header(viewer_token),
    )
    assert dashboard_response.status_code == 200

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("invoices.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount\nF1,2026-04-27,Client,RO1,100\n", "text/csv")},
        headers=auth_header(viewer_token),
    )
    assert upload_response.status_code == 403


def test_mock_anaf_sync_flow():
    _, token = register_user("sync-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Sync Test SRL", "cui": "RO11223344"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("invoices.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount,anaf_status\nSYNC-1,2026-04-27,Client,RO1,100,pending\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200, upload_response.text

    test_response = client.post(
        f"/organizations/{org_id}/integrations/anaf/test",
        headers=auth_header(token),
    )
    assert test_response.status_code == 200
    assert test_response.json()["status"] == "connected"

    sync_response = client.post(
        f"/organizations/{org_id}/invoices/sync-statuses",
        headers=auth_header(token),
    )
    assert sync_response.status_code == 200, sync_response.text
    payload = sync_response.json()
    assert payload["checked"] >= 1
    assert "results" in payload


def test_report_pdf_and_csv_exports():
    _, token = register_user("export-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Export Test SRL", "cui": "RO55667788"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("invoices.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount,anaf_status\nEXP-1,2026-04-27,Client,RO1,100,validated\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200, upload_response.text

    csv_response = client.get(
        f"/organizations/{org_id}/invoices/export.csv",
        headers=auth_header(token),
    )
    assert csv_response.status_code == 200
    assert "invoice_number" in csv_response.text
    assert "EXP-1" in csv_response.text

    pdf_response = client.get(
        f"/organizations/{org_id}/reports/monthly.pdf?year=2026&month=4",
        headers=auth_header(token),
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF")


def test_portfolio_dashboard_summary():
    _, token = register_user("portfolio-owner")

    org_a = client.post(
        "/organizations",
        json={"name": "Portfolio A SRL", "cui": "RO90000001"},
        headers=auth_header(token),
    )
    assert org_a.status_code == 200

    upgrade_response = client.post(
        f"/organizations/{org_a.json()['id']}/subscription",
        json={"plan_code": "starter"},
        headers=auth_header(token),
    )
    assert upgrade_response.status_code == 200, upgrade_response.text

    org_b = client.post(
        "/organizations",
        json={"name": "Portfolio B SRL", "cui": "RO90000002"},
        headers=auth_header(token),
    )
    assert org_b.status_code == 200, org_b.text

    portfolio_response = client.get("/portfolio", headers=auth_header(token))
    assert portfolio_response.status_code == 200
    payload = portfolio_response.json()
    assert payload["total_organizations"] >= 2
    assert "organizations" in payload
    assert any(item["name"] == "Portfolio A SRL" for item in payload["organizations"])

    search_response = client.get("/portfolio?search=Portfolio A", headers=auth_header(token))
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert all("Portfolio A" in item["name"] for item in search_payload["organizations"])


def test_health_and_ready_endpoints():
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"

    ready_response = client.get("/ready")
    assert ready_response.status_code == 200
    assert ready_response.json()["status"] in {"ready", "not_ready"}


def test_invitation_flow_existing_user():
    _, owner_token = register_user("invite-owner")
    invitee_email, invitee_token = register_user("invitee")

    org_response = client.post(
        "/organizations",
        json={"name": "Invite Test SRL", "cui": "RO12399988"},
        headers=auth_header(owner_token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    invite_response = client.post(
        f"/organizations/{org_id}/invitations",
        json={"email": invitee_email, "role": "client_operator"},
        headers=auth_header(owner_token),
    )
    assert invite_response.status_code == 200, invite_response.text
    token = invite_response.json()["token"]

    list_response = client.get(
        f"/organizations/{org_id}/invitations",
        headers=auth_header(owner_token),
    )
    assert list_response.status_code == 200
    assert any(item["invited_email"] == invitee_email for item in list_response.json())

    accept_response = client.post(
        "/invitations/accept",
        json={"token": token},
        headers=auth_header(invitee_token),
    )
    assert accept_response.status_code == 200, accept_response.text
    assert accept_response.json()["status"] == "accepted"

    dashboard_response = client.get(
        f"/organizations/{org_id}/dashboard",
        headers=auth_header(invitee_token),
    )
    assert dashboard_response.status_code == 200


def test_public_invitation_accept_with_account():
    _, owner_token = register_user("public-invite-owner")
    invited_email = unique_email("new-client")

    org_response = client.post(
        "/organizations",
        json={"name": "Public Invite SRL", "cui": "RO77711122"},
        headers=auth_header(owner_token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    invite_response = client.post(
        f"/organizations/{org_id}/invitations",
        json={"email": invited_email, "role": "client_viewer"},
        headers=auth_header(owner_token),
    )
    assert invite_response.status_code == 200, invite_response.text
    token = invite_response.json()["token"]

    public_response = client.get(f"/invitations/public/{token}")
    assert public_response.status_code == 200
    assert public_response.json()["invited_email"] == invited_email

    accept_response = client.post(
        "/invitations/accept-with-account",
        json={"token": token, "name": "New Client", "password": "Password123!"},
    )
    assert accept_response.status_code == 200, accept_response.text
    payload = accept_response.json()
    assert payload["access_token"]
    assert payload["status"] == "accepted"

    dashboard_response = client.get(
        f"/organizations/{org_id}/dashboard",
        headers=auth_header(payload["access_token"]),
    )
    assert dashboard_response.status_code == 200


def test_password_reset_and_change_flow():
    email, token = register_user("password-user")

    request_response = client.post(
        "/auth/password-reset/request",
        json={"email": email},
    )
    assert request_response.status_code == 200

    from app.database import SessionLocal
    from app.models import PasswordResetToken, User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        reset_token = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id)
            .order_by(PasswordResetToken.id.desc())
            .first()
        )
        assert reset_token is not None
        token_value = reset_token.token
    finally:
        db.close()

    confirm_response = client.post(
        "/auth/password-reset/confirm",
        json={"token": token_value, "new_password": "NewPassword123!"},
    )
    assert confirm_response.status_code == 200, confirm_response.text

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "NewPassword123!"},
    )
    assert login_response.status_code == 200

    new_access_token = login_response.json()["access_token"]

    change_response = client.post(
        "/auth/password-change",
        json={"current_password": "NewPassword123!", "new_password": "FinalPassword123!"},
        headers=auth_header(new_access_token),
    )
    assert change_response.status_code == 200

    final_login = client.post(
        "/auth/login",
        json={"email": email, "password": "FinalPassword123!"},
    )
    assert final_login.status_code == 200


def test_uploaded_document_is_stored_and_downloadable():
    _, token = register_user("document-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Document Test SRL", "cui": "RO44112233"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("doc-test.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount,anaf_status\nDOC-1,2026-04-27,Client,RO1,100,validated\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200, upload_response.text

    documents_response = client.get(
        f"/organizations/{org_id}/documents",
        headers=auth_header(token),
    )
    assert documents_response.status_code == 200
    documents = documents_response.json()
    assert len(documents) >= 1
    document_id = documents[0]["id"]

    download_response = client.get(
        f"/organizations/{org_id}/documents/{document_id}/download",
        headers=auth_header(token),
    )
    assert download_response.status_code == 200
    assert b"DOC-1" in download_response.content


def test_s3_uri_parser():
    from app.file_storage import parse_s3_uri

    bucket, key = parse_s3_uri("s3://my-bucket/organizations/1/file.xml")
    assert bucket == "my-bucket"
    assert key == "organizations/1/file.xml"


def test_billing_plans_subscription_and_usage():
    _, token = register_user("billing-owner")

    plans_response = client.get("/billing/plans")
    assert plans_response.status_code == 200
    assert any(plan["code"] == "free" for plan in plans_response.json())

    org_response = client.post(
        "/organizations",
        json={"name": "Billing Test SRL", "cui": "RO88001122"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    subscription_response = client.get(
        f"/organizations/{org_id}/subscription",
        headers=auth_header(token),
    )
    assert subscription_response.status_code == 200
    assert subscription_response.json()["plan_code"] == "free"

    update_response = client.post(
        f"/organizations/{org_id}/subscription",
        json={"plan_code": "starter"},
        headers=auth_header(token),
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["plan_code"] == "starter"

    usage_response = client.get(
        f"/organizations/{org_id}/usage",
        headers=auth_header(token),
    )
    assert usage_response.status_code == 200
    assert usage_response.json()["plan_code"] == "starter"


def test_netopia_mock_checkout_and_webhook_activates_plan():
    _, token = register_user("netopia-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Netopia Test SRL", "cui": "RO55119922"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    checkout_response = client.post(
        f"/organizations/{org_id}/billing/netopia-mock/checkout",
        json={"plan_code": "pro"},
        headers=auth_header(token),
    )
    assert checkout_response.status_code == 200, checkout_response.text
    checkout = checkout_response.json()
    assert checkout["status"] == "pending"
    assert checkout["provider"] == "netopia_mock"

    webhook_response = client.post(
        "/billing/netopia-mock/webhook",
        json={
            "session_id": checkout["provider_session_id"],
            "status": "paid",
            "secret": "dev-netopia-webhook-secret",
        },
    )
    assert webhook_response.status_code == 200, webhook_response.text
    assert webhook_response.json()["status"] == "paid"

    subscription_response = client.get(
        f"/organizations/{org_id}/subscription",
        headers=auth_header(token),
    )
    assert subscription_response.status_code == 200
    assert subscription_response.json()["plan_code"] == "pro"


def test_onboarding_status_progression():
    _, token = register_user("onboarding-user")

    initial = client.get("/onboarding/status", headers=auth_header(token))
    assert initial.status_code == 200
    assert initial.json()["next_step"] == "create_organization"

    org_response = client.post(
        "/organizations",
        json={"name": "Onboarding Test SRL", "cui": "RO91919191"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    after_org = client.get("/onboarding/status", headers=auth_header(token))
    assert after_org.status_code == 200
    assert after_org.json()["next_step"] == "upload_invoices"

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("onboarding.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount,anaf_status\nONB-1,2026-04-27,Client,RO1,100,pending\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200

    after_upload = client.get("/onboarding/status", headers=auth_header(token))
    assert after_upload.status_code == 200
    assert after_upload.json()["next_step"] == "run_sync"


def test_audit_summary_and_csv_export():
    _, token = register_user("audit-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Audit Test SRL", "cui": "RO33112244"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    summary_response = client.get(
        f"/organizations/{org_id}/audit-summary",
        headers=auth_header(token),
    )
    assert summary_response.status_code == 200
    assert summary_response.json()["total_events"] >= 1

    logs_response = client.get(
        f"/organizations/{org_id}/audit-logs?action=organization",
        headers=auth_header(token),
    )
    assert logs_response.status_code == 200

    csv_response = client.get(
        f"/organizations/{org_id}/audit-logs/export.csv",
        headers=auth_header(token),
    )
    assert csv_response.status_code == 200
    assert "action" in csv_response.text
    assert "organization.created" in csv_response.text


def test_notification_settings_update():
    _, token = register_user("settings-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Settings Test SRL", "cui": "RO11993322"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    get_response = client.get(
        f"/organizations/{org_id}/notification-settings",
        headers=auth_header(token),
    )
    assert get_response.status_code == 200
    assert get_response.json()["email_alerts_enabled"] is True

    update_response = client.put(
        f"/organizations/{org_id}/notification-settings",
        json={
            "email_alerts_enabled": False,
            "alert_email": "alerts@example.com",
            "near_deadline_days": 5,
            "daily_digest_enabled": True,
        },
        headers=auth_header(token),
    )
    assert update_response.status_code == 200, update_response.text
    payload = update_response.json()
    assert payload["email_alerts_enabled"] is False
    assert payload["alert_email"] == "alerts@example.com"
    assert payload["near_deadline_days"] == 5
    assert payload["daily_digest_enabled"] is True


def test_daily_digest_preview_and_send():
    _, token = register_user("digest-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Digest Test SRL", "cui": "RO88776655"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    settings_response = client.put(
        f"/organizations/{org_id}/notification-settings",
        json={
            "email_alerts_enabled": True,
            "alert_email": "digest@example.com",
            "daily_digest_enabled": True,
        },
        headers=auth_header(token),
    )
    assert settings_response.status_code == 200

    preview_response = client.get(
        f"/organizations/{org_id}/digest/preview",
        headers=auth_header(token),
    )
    assert preview_response.status_code == 200
    assert "FacturaGuard daily digest" in preview_response.json()["subject"]

    send_response = client.post(
        f"/organizations/{org_id}/digest/send?force=true",
        headers=auth_header(token),
    )
    assert send_response.status_code == 200, send_response.text
    assert send_response.json()["sent"] is True


def test_client_portal_read_only_access():
    _, owner_token = register_user("portal-owner")
    client_email, client_token = register_user("portal-client")

    org_response = client.post(
        "/organizations",
        json={"name": "Portal Test SRL", "cui": "RO22334455"},
        headers=auth_header(owner_token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    invite_response = client.post(
        f"/organizations/{org_id}/invitations",
        json={"email": client_email, "role": "client_viewer"},
        headers=auth_header(owner_token),
    )
    assert invite_response.status_code == 200
    token_value = invite_response.json()["token"]

    accept_response = client.post(
        "/invitations/accept",
        json={"token": token_value},
        headers=auth_header(client_token),
    )
    assert accept_response.status_code == 200

    portal_response = client.get(
        "/client-portal",
        headers=auth_header(client_token),
    )
    assert portal_response.status_code == 200
    assert any(org["id"] == org_id for org in portal_response.json()["organizations"])

    detail_response = client.get(
        f"/client-portal/organizations/{org_id}",
        headers=auth_header(client_token),
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["organization"]["id"] == org_id

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("portal.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount\nP-1,2026-04-27,Client,RO1,100\n", "text/csv")},
        headers=auth_header(client_token),
    )
    assert upload_response.status_code == 403


def test_saved_views_crud():
    _, token = register_user("views-user")

    create_response = client.post(
        "/saved-views",
        json={
            "name": "Risc mare",
            "view_type": "portfolio",
            "filters": {"risk": "high", "search": ""},
            "is_default": True,
        },
        headers=auth_header(token),
    )
    assert create_response.status_code == 200, create_response.text
    view_id = create_response.json()["id"]

    list_response = client.get(
        "/saved-views?view_type=portfolio",
        headers=auth_header(token),
    )
    assert list_response.status_code == 200
    assert any(view["id"] == view_id for view in list_response.json())

    update_response = client.put(
        f"/saved-views/{view_id}",
        json={"name": "Risc mare actualizat", "filters": {"risk": "high"}},
        headers=auth_header(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Risc mare actualizat"

    delete_response = client.delete(
        f"/saved-views/{view_id}",
        headers=auth_header(token),
    )
    assert delete_response.status_code == 200


def test_bulk_invoice_action_sync_and_resolve_alerts():
    _, token = register_user("bulk-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Bulk Test SRL", "cui": "RO12344321"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("bulk.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount,anaf_status,anaf_message\nBULK-1,2026-04-27,Client,RO1,100,rejected,CUI invalid\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200, upload_response.text
    invoice_id = upload_response.json()[0]["id"]

    bulk_response = client.post(
        f"/organizations/{org_id}/invoices/bulk-action",
        json={"invoice_ids": [invoice_id], "action": "resolve_related_alerts"},
        headers=auth_header(token),
    )
    assert bulk_response.status_code == 200, bulk_response.text
    assert bulk_response.json()["processed"] == 1

    alerts_response = client.get(
        f"/organizations/{org_id}/alerts?status=open",
        headers=auth_header(token),
    )
    assert alerts_response.status_code == 200


def test_invoice_notes_flow():
    _, token = register_user("notes-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Notes Test SRL", "cui": "RO55443322"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("notes.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount\nNOTE-1,2026-04-27,Client,RO1,100\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200, upload_response.text
    invoice_id = upload_response.json()[0]["id"]

    create_note = client.post(
        f"/organizations/{org_id}/invoices/{invoice_id}/notes",
        json={"body": "Clientul a confirmat corectura.", "is_internal": False},
        headers=auth_header(token),
    )
    assert create_note.status_code == 200, create_note.text
    assert create_note.json()["body"] == "Clientul a confirmat corectura."

    list_notes = client.get(
        f"/organizations/{org_id}/invoices/{invoice_id}/notes",
        headers=auth_header(token),
    )
    assert list_notes.status_code == 200
    assert len(list_notes.json()) >= 1


def test_invoice_metadata_update():
    _, token = register_user("metadata-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Metadata Test SRL", "cui": "RO66778899"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("metadata.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount\nMETA-1,2026-04-27,Client,RO1,100\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200, upload_response.text
    invoice_id = upload_response.json()[0]["id"]

    update_response = client.put(
        f"/organizations/{org_id}/invoices/{invoice_id}/metadata",
        json={"tags": "urgent, client-important", "priority": "urgent"},
        headers=auth_header(token),
    )
    assert update_response.status_code == 200, update_response.text
    payload = update_response.json()
    assert payload["tags"] == "urgent,client-important"
    assert payload["priority"] == "urgent"


def test_work_queue_filters():
    _, token = register_user("queue-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "Queue Test SRL", "cui": "RO99887766"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    upload_response = client.post(
        f"/organizations/{org_id}/invoices/upload",
        files={"file": ("queue.csv", "invoice_number,issue_date,customer_name,customer_cui,total_amount,anaf_status,anaf_message\nQUEUE-1,2026-04-27,Client,RO1,100,rejected,CUI invalid\n", "text/csv")},
        headers=auth_header(token),
    )
    assert upload_response.status_code == 200, upload_response.text
    invoice_id = upload_response.json()[0]["id"]

    metadata_response = client.put(
        f"/organizations/{org_id}/invoices/{invoice_id}/metadata",
        json={"tags": "urgent,client-important", "priority": "urgent"},
        headers=auth_header(token),
    )
    assert metadata_response.status_code == 200

    queue_response = client.get(
        f"/organizations/{org_id}/work-queue?priority=urgent&tag=urgent",
        headers=auth_header(token),
    )
    assert queue_response.status_code == 200
    payload = queue_response.json()
    assert payload["total"] >= 1
    assert payload["urgent"] >= 1


def test_system_status_endpoint():
    _, token = register_user("system-status-user")

    response = client.get(
        "/system/status",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["database"] in {"ok", "error"}
    assert "app_version" in payload
    assert "total_organizations" in payload


def test_api_key_create_public_invoice_and_revoke():
    _, token = register_user("api-key-owner")

    org_response = client.post(
        "/organizations",
        json={"name": "API Key Test SRL", "cui": "RO10101010"},
        headers=auth_header(token),
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]

    create_key_response = client.post(
        f"/organizations/{org_id}/api-keys",
        json={"name": "ERP", "scopes": "invoices:write"},
        headers=auth_header(token),
    )
    assert create_key_response.status_code == 200, create_key_response.text
    raw_key = create_key_response.json()["raw_key"]
    key_id = create_key_response.json()["id"]

    public_response = client.post(
        "/public-api/v1/invoices",
        json={
            "invoice_number": "API-1",
            "issue_date": "2026-04-27",
            "customer_name": "API Client",
            "customer_cui": "RO1",
            "total_amount": 123.45,
            "anaf_status": "pending",
        },
        headers={"X-API-Key": raw_key},
    )
    assert public_response.status_code == 200, public_response.text
    assert public_response.json()["invoice_number"] == "API-1"

    revoke_response = client.post(
        f"/organizations/{org_id}/api-keys/{key_id}/revoke",
        headers=auth_header(token),
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"

    public_after_revoke = client.post(
        "/public-api/v1/invoices",
        json={
            "invoice_number": "API-2",
            "issue_date": "2026-04-27",
            "customer_name": "API Client",
            "customer_cui": "RO1",
            "total_amount": 123.45,
        },
        headers={"X-API-Key": raw_key},
    )
    assert public_after_revoke.status_code == 401


def test_import_templates_download():
    csv_response = client.get("/templates/invoices.csv")
    assert csv_response.status_code == 200
    assert "invoice_number" in csv_response.text
    assert "FG-001" in csv_response.text

    xml_response = client.get("/templates/invoices.xml")
    assert xml_response.status_code == 200
    assert "<invoices>" in xml_response.text

    zip_response = client.get("/templates/facturaguard-import-templates.zip")
    assert zip_response.status_code == 200
    assert zip_response.headers["content-type"].startswith("application/zip")
