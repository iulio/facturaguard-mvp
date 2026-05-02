from datetime import date, datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class OrganizationCreate(BaseModel):
    name: str
    cui: str
    address: str | None = None

class OrganizationOut(BaseModel):
    id: int
    name: str
    cui: str
    address: str | None = None

    class Config:
        from_attributes = True

class OrganizationMemberCreate(BaseModel):
    email: EmailStr
    role: str = "client_viewer"

class OrganizationMemberOut(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceOut(BaseModel):
    id: int
    organization_id: int
    invoice_number: str
    issue_date: date
    due_submission_date: date
    customer_name: str
    customer_cui: str
    total_amount: float
    currency: str
    source: str
    internal_status: str
    anaf_status: str
    anaf_message: str | None = None
    plain_explanation: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    organization_id: int
    invoice_id: int | None
    alert_type: str
    severity: str
    title: str
    message: str
    status: str
    sent_email: bool
    created_at: datetime
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: int
    organization_id: int
    actor_user_id: int | None
    action: str
    entity_type: str | None
    entity_id: str | None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardSummary(BaseModel):
    total_invoices: int
    validated: int
    rejected: int
    unsent: int
    near_deadline: int
    overdue: int
    open_alerts: int

class MonthlyReport(BaseModel):
    organization_id: int
    year: int
    month: int
    total_invoices: int
    validated: int
    rejected: int
    unsent: int
    near_deadline: int
    overdue: int
    total_amount: float
    top_errors: list[dict]
    recommendations: list[str]
