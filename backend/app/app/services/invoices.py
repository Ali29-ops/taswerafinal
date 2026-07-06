"""Invoice receipt generation."""

import base64
import io
from pathlib import Path

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import generate_secure_token
from app.models.sale import Sale

settings = get_settings()


def invoice_url(token: str) -> str:
    return f"{settings.frontend_url}/invoice/{token}"


def invoice_download_url(token: str) -> str:
    return f"{settings.frontend_url}/api/v1/portal/invoices/{token}/download"


def invoice_qr_data_url(token: str) -> tuple[str, str]:
    url = invoice_url(token)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return url, f"data:image/png;base64,{b64}"


async def ensure_invoice_token(db: AsyncSession, sale: Sale) -> str:
    if sale.invoice_token:
        return sale.invoice_token
    while True:
        token = generate_secure_token(24)
        existing = await db.execute(select(Sale.id).where(Sale.invoice_token == token))
        if not existing.scalar_one_or_none():
            sale.invoice_token = token
            await db.flush()
            return token


def _logo_path() -> str | None:
    candidates = [
        Path("/app/assets/logo.jpg"),
        Path("/app/taswera-logo.jpg"),
    ]
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidates.append(parent / "logo.jpg")
        candidates.append(parent / "frontend" / "public" / "taswera-logo.jpg")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def generate_invoice_pdf(sale: Sale) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=34,
        bottomMargin=34,
    )
    styles = getSampleStyleSheet()
    elements = []

    logo = _logo_path()
    if logo:
        elements.append(Image(logo, width=1.8 * inch, height=0.8 * inch, kind="proportional"))
        elements.append(Spacer(1, 8))

    elements.append(Paragraph("<b>TASWERA</b>", styles["Title"]))
    elements.append(Paragraph("Print Order Invoice / Receipt", styles["Heading2"]))
    elements.append(Spacer(1, 14))

    customer_name = sale.customer.name if sale.customer else f"Customer #{sale.customer_id}"
    employee_name = f"{sale.employee.first_name} {sale.employee.last_name}" if sale.employee else f"Employee #{sale.employee_id}"
    branch_name = sale.branch.name if sale.branch else "-"

    summary = [
        ["Invoice No.", f"INV-{sale.id:06d}"],
        ["Date", sale.created_at.strftime("%Y-%m-%d %H:%M")],
        ["Customer", customer_name],
        ["Employee", employee_name],
        ["Branch", branch_name],
    ]
    summary_table = Table(summary, colWidths=[1.5 * inch, 4.7 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 18))

    rows = [
        ["Item", "Count", "Unit Price", "Total"],
        ["Small Images", sale.small_photo_count, f"EGP {sale.price_per_photo:.2f}", f"EGP {sale.small_photo_count * sale.price_per_photo:.2f}"],
        ["Large Images", sale.large_photo_count, f"EGP {sale.price_per_photo:.2f}", f"EGP {sale.large_photo_count * sale.price_per_photo:.2f}"],
        ["Total Photos", sale.photo_count, "", f"EGP {sale.amount:.2f}"],
    ]
    items_table = Table(rows, colWidths=[2.2 * inch, 1.1 * inch, 1.5 * inch, 1.5 * inch])
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(items_table)

    if sale.notes:
        elements.append(Spacer(1, 14))
        elements.append(Paragraph(f"<b>Notes:</b> {sale.notes}", styles["BodyText"]))

    elements.append(Spacer(1, 22))
    elements.append(Paragraph("Thank you for choosing TASWERA.", styles["BodyText"]))

    doc.build(elements)
    return buffer.getvalue()
