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

    org_b = client.post(
        "/organizations",
        json={"name": "Portfolio B SRL", "cui": "RO90000002"},
        headers=auth_header(token),
    )
    assert org_b.status_code == 200

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
