import io
import zipfile

CSV_TEMPLATE = """invoice_number,issue_date,customer_name,customer_cui,total_amount,currency,anaf_status,anaf_message
FG-001,2026-04-27,Client Demo SRL,RO12345678,1200.50,RON,pending,
FG-002,2026-04-28,Client Problem SRL,RO00000000,850.00,RON,rejected,CUI invalid
FG-003,2026-04-29,Client Valid SRL,RO87654321,3400.00,RON,validated,
"""

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<invoices>
  <invoice>
    <invoice_number>FG-XML-001</invoice_number>
    <issue_date>2026-04-27</issue_date>
    <customer_name>Client XML SRL</customer_name>
    <customer_cui>RO12345678</customer_cui>
    <total_amount>1200.50</total_amount>
    <currency>RON</currency>
    <anaf_status>pending</anaf_status>
    <anaf_message></anaf_message>
  </invoice>
  <invoice>
    <invoice_number>FG-XML-002</invoice_number>
    <issue_date>2026-04-28</issue_date>
    <customer_name>Client Respins SRL</customer_name>
    <customer_cui>RO00000000</customer_cui>
    <total_amount>850.00</total_amount>
    <currency>RON</currency>
    <anaf_status>rejected</anaf_status>
    <anaf_message>CUI invalid</anaf_message>
  </invoice>
</invoices>
"""

README_TEMPLATE = """FacturaGuard import templates

CSV required columns:
- invoice_number
- issue_date
- customer_name
- customer_cui
- total_amount

Optional columns:
- currency
- anaf_status
- anaf_message

Date format:
YYYY-MM-DD

Supported statuses:
- pending
- validated
- rejected

Upload these files from the FacturaGuard dashboard or onboarding page.
"""

def build_templates_zip() -> bytes:
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("facturaguard-template.csv", CSV_TEMPLATE)
        archive.writestr("facturaguard-template.xml", XML_TEMPLATE)
        archive.writestr("README.txt", README_TEMPLATE)

    buffer.seek(0)
    return buffer.read()
