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
