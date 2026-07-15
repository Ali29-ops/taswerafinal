"""Public customer portal via QR token."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.customer import Customer
from app.models.photo import Photo
from app.models.sale import Sale
from app.schemas import CustomerPortalResponse, CustomerResponse, PhotoResponse, SaleResponse
from app.services.invoices import ensure_invoice_token, generate_invoice_pdf, invoice_url
from app.services.storage import get_storage
from app.utils.urls import public_base_url

router = APIRouter(prefix="/portal", tags=["Customer Portal"])


@router.get("/{token}", response_model=CustomerPortalResponse)
async def customer_portal(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Customer)
        .options(selectinload(Customer.photos), selectinload(Customer.sales))
        .where(Customer.qr_token == token)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Invalid or expired link")

    storage = get_storage()
    photos = []
    for photo in customer.photos:
        p = PhotoResponse.model_validate(photo)
        p.url = f"/api/v1/portal/{token}/photos/{photo.id}/view"
        photos.append(p)

    sales = []
    for s in customer.sales:
        token = await ensure_invoice_token(db, s)
        sales.append(
            SaleResponse(
                id=s.id,
                customer_id=s.customer_id,
                employee_id=s.employee_id,
                small_photo_count=s.small_photo_count,
                large_photo_count=s.large_photo_count,
                photo_count=s.photo_count,
                price_per_photo=s.price_per_photo,
                amount=s.amount,
                notes=s.notes,
                created_at=s.created_at,
                invoice_url=invoice_url(token, public_base_url(request)),
            )
        )
    return CustomerPortalResponse(
        customer=CustomerResponse.model_validate(customer),
        photos=photos,
        sales=sales,
    )


@router.get("/{token}/photos/{photo_id}/view")
async def view_photo(token: str, photo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Photo)
        .join(Customer, Photo.customer_id == Customer.id)
        .where(Customer.qr_token == token, Photo.id == photo_id)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    storage = get_storage()
    content = await storage.read(photo.file_path)
    return Response(content=content, media_type=photo.mime_type)


@router.get("/{token}/photos/{photo_id}/download")
async def download_photo(token: str, photo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Customer).options(selectinload(Customer.photos)).where(Customer.qr_token == token)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Invalid link")
    photo = next((p for p in customer.photos if p.id == photo_id), None)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    storage = get_storage()
    content = await storage.read(photo.file_path)
    return Response(
        content=content,
        media_type=photo.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{photo.file_name}"'},
    )


@router.get("/invoices/{token}/download")
async def download_invoice(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Sale)
        .options(selectinload(Sale.customer), selectinload(Sale.employee), selectinload(Sale.branch), selectinload(Sale.package))
        .where(Sale.invoice_token == token)
    )
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
    content = generate_invoice_pdf(sale)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="taswera_invoice_{sale.id}.pdf"'},
    )
