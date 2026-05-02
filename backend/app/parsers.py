import csv, io, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

def parse_csv_upload(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {"invoice_number", "issue_date", "customer_name", "customer_cui", "total_amount"}
    if not required.issubset(set(reader.fieldnames or [])):
        missing = required - set(reader.fieldnames or [])
        raise ValueError(f"Lipsesc coloane obligatorii: {', '.join(sorted(missing))}")
    out = []
    for row in reader:
        out.append({
            "invoice_number": row["invoice_number"].strip(),
            "issue_date": datetime.strptime(row["issue_date"].strip(), "%Y-%m-%d").date(),
            "customer_name": row["customer_name"].strip(),
            "customer_cui": row["customer_cui"].strip(),
            "total_amount": float(row["total_amount"]),
            "currency": (row.get("currency") or "RON").strip(),
            "anaf_status": (row.get("anaf_status") or "pending").strip().lower(),
            "anaf_message": (row.get("anaf_message") or "").strip() or None,
        })
    return out

def _local_name(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag

def _all(root: ET.Element, local_name: str):
    return [node for node in root.iter() if _local_name(node.tag) == local_name]

def _first_text(root: ET.Element, names: list[str], default=None):
    for name in names:
        for node in _all(root, name):
            if node.text and node.text.strip():
                return node.text.strip()
    return default

def _first_text_under(parent: ET.Element, names: list[str], default=None):
    for name in names:
        for node in parent.iter():
            if _local_name(node.tag) == name and node.text and node.text.strip():
                return node.text.strip()
    return default

def _find_customer(root: ET.Element):
    nodes = _all(root, "AccountingCustomerParty")
    if nodes:
        customer = nodes[0]
        name = _first_text_under(customer, ["RegistrationName", "Name"], "Client necunoscut")
        cui = _first_text_under(customer, ["CompanyID", "ID"], "N/A")
        return name, cui
    return (
        _first_text(root, ["CustomerName", "RegistrationName", "Name"], "Client necunoscut"),
        _first_text(root, ["CustomerCUI", "CompanyID"], "N/A"),
    )

def parse_xml_upload(content: bytes) -> list[dict]:
    root = ET.fromstring(content)
    invoice_number = _first_text(root, ["InvoiceNumber", "ID"], "FARA-NUMAR")
    issue_date_raw = _first_text(root, ["IssueDate"], None)
    if not issue_date_raw:
        raise ValueError("XML-ul nu conține IssueDate.")
    customer_name, customer_cui = _find_customer(root)
    total_amount = _first_text(root, ["TotalAmount", "PayableAmount", "TaxInclusiveAmount"], "0")
    currency = _first_text(root, ["Currency", "DocumentCurrencyCode"], "RON")
    anaf_status = _first_text(root, ["AnafStatus"], "pending")
    anaf_message = _first_text(root, ["AnafMessage"], None)
    return [{
        "invoice_number": invoice_number,
        "issue_date": datetime.strptime(issue_date_raw, "%Y-%m-%d").date(),
        "customer_name": customer_name,
        "customer_cui": customer_cui,
        "total_amount": float(str(total_amount).replace(",", ".")),
        "currency": currency,
        "anaf_status": anaf_status.lower(),
        "anaf_message": anaf_message,
    }]

def parse_zip_upload(content: bytes) -> list[dict]:
    invoices, errors = [], []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        xml_files = [name for name in archive.namelist() if name.lower().endswith(".xml") and not name.endswith("/")]
        if not xml_files:
            raise ValueError("ZIP-ul nu conține fișiere XML.")
        for name in xml_files:
            try:
                parsed = parse_xml_upload(archive.read(name))
                for item in parsed:
                    item["source_file"] = name
                invoices.extend(parsed)
            except Exception as exc:
                errors.append(f"{name}: {exc}")
    if not invoices and errors:
        raise ValueError("Nu s-a putut importa niciun XML din ZIP: " + "; ".join(errors))
    return invoices
