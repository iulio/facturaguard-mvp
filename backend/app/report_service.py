import csv
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .models import Invoice, Organization
from .services import build_monthly_report

def generate_invoices_csv(invoices: list[Invoice]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "invoice_number",
        "issue_date",
        "due_submission_date",
        "customer_name",
        "customer_cui",
        "total_amount",
        "currency",
        "internal_status",
        "anaf_status",
        "anaf_upload_id",
        "last_synced_at",
        "anaf_message",
    ])

    for invoice in invoices:
        writer.writerow([
            invoice.invoice_number,
            invoice.issue_date.isoformat(),
            invoice.due_submission_date.isoformat(),
            invoice.customer_name,
            invoice.customer_cui,
            f"{invoice.total_amount:.2f}",
            invoice.currency,
            invoice.internal_status,
            invoice.anaf_status,
            invoice.anaf_upload_id or "",
            invoice.last_synced_at.isoformat() if invoice.last_synced_at else "",
            invoice.anaf_message or "",
        ])

    return output.getvalue()

def generate_monthly_report_pdf(
    organization: Organization,
    year: int,
    month: int,
    invoices: list[Invoice],
) -> bytes:
    report = build_monthly_report(organization.id, year, month, invoices)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"FacturaGuard raport {organization.name} {year}-{month:02d}",
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("FacturaGuard - Raport lunar e-Factura", styles["Title"]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(f"Firma: <b>{organization.name}</b>", styles["Normal"]))
    story.append(Paragraph(f"CUI: <b>{organization.cui}</b>", styles["Normal"]))
    story.append(Paragraph(f"Perioada: <b>{year}-{month:02d}</b>", styles["Normal"]))
    story.append(Paragraph(f"Generat la: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    summary_data = [
        ["Indicator", "Valoare"],
        ["Total facturi", report["total_invoices"]],
        ["Validate", report["validated"]],
        ["Respinse", report["rejected"]],
        ["Netrimise", report["unsent"]],
        ["Aproape de termen", report["near_deadline"]],
        ["Depasite", report["overdue"]],
        ["Valoare totala", f'{report["total_amount"]:.2f} RON'],
    ]

    summary_table = Table(summary_data, colWidths=[9 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Top erori", styles["Heading2"]))
    if report["top_errors"]:
        error_data = [["Eroare", "Numar"]] + [
            [item["error"], item["count"]]
            for item in report["top_errors"]
        ]
    else:
        error_data = [["Eroare", "Numar"], ["Nu exista erori recurente.", "0"]]

    error_table = Table(error_data, colWidths=[12 * cm, 3 * cm])
    error_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(error_table)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Recomandari", styles["Heading2"]))
    for recommendation in report["recommendations"]:
        story.append(Paragraph(f"- {recommendation}", styles["Normal"]))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Facturi cu probleme", styles["Heading2"]))

    problem_invoices = [
        invoice for invoice in invoices
        if invoice.issue_date.year == year
        and invoice.issue_date.month == month
        and invoice.internal_status != "validated"
    ][:20]

    if problem_invoices:
        invoice_data = [["Factura", "Client", "Status", "Deadline", "Total"]]
        for invoice in problem_invoices:
            invoice_data.append([
                invoice.invoice_number,
                invoice.customer_name[:32],
                invoice.internal_status,
                invoice.due_submission_date.isoformat(),
                f"{invoice.total_amount:.2f} {invoice.currency}",
            ])
    else:
        invoice_data = [["Factura", "Client", "Status", "Deadline", "Total"], ["-", "Nu exista facturi cu probleme.", "-", "-", "-"]]

    invoice_table = Table(invoice_data, colWidths=[2.8 * cm, 5.3 * cm, 3 * cm, 2.8 * cm, 3 * cm])
    invoice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(invoice_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
