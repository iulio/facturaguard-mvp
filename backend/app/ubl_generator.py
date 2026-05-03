from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace
from xml.dom import minidom

from .models import Invoice, Organization

UBL_INVOICE_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

register_namespace("", UBL_INVOICE_NS)
register_namespace("cac", CAC_NS)
register_namespace("cbc", CBC_NS)

def qname(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"

def cbc(parent: Element, tag: str, text: str | int | float | Decimal | None = None, **attrib) -> Element:
    node = SubElement(parent, qname(CBC_NS, tag), attrib)
    if text is not None:
        node.text = str(text)
    return node

def cac(parent: Element, tag: str) -> Element:
    return SubElement(parent, qname(CAC_NS, tag))

def money(value: float | Decimal) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return str(amount)

def normalize_cui(value: str | None) -> str:
    if not value:
        return ""
    return value.upper().replace("RO", "").replace(" ", "").strip()

def build_basic_ubl_invoice_xml(
    invoice: Invoice,
    supplier: Organization,
    supplier_name: str | None = None,
    supplier_cui: str | None = None,
    supplier_country: str = "RO",
) -> str:
    """Build a minimal UBL-like invoice XML.

    This is intentionally a skeleton for integration work. It is not a full
    Romanian CIUS-RO compliant e-Factura generator yet. Before production use,
    validate generated XML against the official ANAF validator and complete
    supplier/customer addresses, VAT categories, tax subtotals, payment means,
    line-level product details and CIUS-RO business rules.
    """

    supplier_name = supplier_name or supplier.name
    supplier_cui = supplier_cui or supplier.cui
    currency = invoice.currency or "RON"
    total = money(invoice.total_amount)

    root = Element(qname(UBL_INVOICE_NS, "Invoice"))

    cbc(root, "CustomizationID", "urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1")
    cbc(root, "ProfileID", "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0")
    cbc(root, "ID", invoice.invoice_number)
    cbc(root, "IssueDate", invoice.issue_date.isoformat() if isinstance(invoice.issue_date, date) else str(invoice.issue_date))
    cbc(root, "InvoiceTypeCode", "380")
    cbc(root, "DocumentCurrencyCode", currency)

    supplier_party = cac(root, "AccountingSupplierParty")
    supplier_party_node = cac(supplier_party, "Party")
    supplier_endpoint = cbc(supplier_party_node, "EndpointID", normalize_cui(supplier_cui), schemeID="RO:CUI")
    party_tax_scheme = cac(supplier_party_node, "PartyTaxScheme")
    cbc(party_tax_scheme, "CompanyID", normalize_cui(supplier_cui))
    tax_scheme = cac(party_tax_scheme, "TaxScheme")
    cbc(tax_scheme, "ID", "VAT")

    party_legal_entity = cac(supplier_party_node, "PartyLegalEntity")
    cbc(party_legal_entity, "RegistrationName", supplier_name)
    cbc(party_legal_entity, "CompanyID", normalize_cui(supplier_cui))

    supplier_address = cac(supplier_party_node, "PostalAddress")
    cbc(supplier_address, "StreetName", supplier.address or "Adresă necompletată")
    country = cac(supplier_address, "Country")
    cbc(country, "IdentificationCode", supplier_country)

    customer_party = cac(root, "AccountingCustomerParty")
    customer_party_node = cac(customer_party, "Party")
    cbc(customer_party_node, "EndpointID", normalize_cui(invoice.customer_cui), schemeID="RO:CUI")

    customer_tax_scheme = cac(customer_party_node, "PartyTaxScheme")
    cbc(customer_tax_scheme, "CompanyID", normalize_cui(invoice.customer_cui))
    customer_tax = cac(customer_tax_scheme, "TaxScheme")
    cbc(customer_tax, "ID", "VAT")

    customer_legal_entity = cac(customer_party_node, "PartyLegalEntity")
    cbc(customer_legal_entity, "RegistrationName", invoice.customer_name)
    cbc(customer_legal_entity, "CompanyID", normalize_cui(invoice.customer_cui))

    customer_address = cac(customer_party_node, "PostalAddress")
    cbc(customer_address, "StreetName", "Adresă client necompletată")
    customer_country = cac(customer_address, "Country")
    cbc(customer_country, "IdentificationCode", "RO")

    tax_total = cac(root, "TaxTotal")
    cbc(tax_total, "TaxAmount", "0.00", currencyID=currency)

    legal_monetary_total = cac(root, "LegalMonetaryTotal")
    cbc(legal_monetary_total, "LineExtensionAmount", total, currencyID=currency)
    cbc(legal_monetary_total, "TaxExclusiveAmount", total, currencyID=currency)
    cbc(legal_monetary_total, "TaxInclusiveAmount", total, currencyID=currency)
    cbc(legal_monetary_total, "PayableAmount", total, currencyID=currency)

    invoice_line = cac(root, "InvoiceLine")
    cbc(invoice_line, "ID", "1")
    cbc(invoice_line, "InvoicedQuantity", "1", unitCode="H87")
    cbc(invoice_line, "LineExtensionAmount", total, currencyID=currency)

    item = cac(invoice_line, "Item")
    cbc(item, "Name", f"Servicii / produse factura {invoice.invoice_number}")

    price = cac(invoice_line, "Price")
    cbc(price, "PriceAmount", total, currencyID=currency)

    raw = tostring(root, encoding="utf-8", xml_declaration=True)
    return minidom.parseString(raw).toprettyxml(indent="  ")

def build_ubl_filename(invoice: Invoice) -> str:
    safe_number = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in invoice.invoice_number)
    return f"efactura-{safe_number}.xml"
