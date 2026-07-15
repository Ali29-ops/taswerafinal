"""Photo upload and management routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.customer import Customer
from app.models.photo import Photo
from app.models.user import User
from app.schemas import MessageResponse, PaginatedResponse, PhotoResponse
from app.services.audit import log_action
from app.services.photo_cleanup import cleanup_expired_photos
from app.services.storage import get_storage
from app.utils.helpers import get_manager_employee_ids, paginate, pagination_meta

router = APIRouter(prefix="/photos", tags=["Photos"])
settings = get_settings()


def detect_image_mime(content: bytes) -> str:
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    raise HTTPException(status_code=400, detail="Invalid image type. Allowed: JPG, PNG, WEBP")


def validate_image(content: bytes) -> str:
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")
    return detect_image_mime(content)


async def _scoped_photo_query(current_user: User, db: AsyncSession):
    stmt = select(Photo)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Photo.uploaded_by_employee_id == current_user.id)
    elif current_user.role == UserRole.MANAGER.value:
        employee_ids = await get_manager_employee_ids(db, current_user.id)
        stmt = stmt.where(Photo.uploaded_by_employee_id.in_(employee_ids or [-1]))
    return stmt


@router.get("", response_model=PaginatedResponse[PhotoResponse])
async def list_photos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = await _scoped_photo_query(current_user, db)
    if customer_id:
        stmt = stmt.where(Photo.customer_id == customer_id)
    stmt = stmt.order_by(Photo.created_at.desc())
    items, total = await paginate(db, stmt, page, page_size)
    storage = get_storage()
    responses = []
    for photo in items:
        data = PhotoResponse.model_validate(photo)
        data.url = storage.get_url(photo.file_path)
        responses.append(data)
    return PaginatedResponse(items=responses, **pagination_meta(total, page, page_size))


@router.post("/upload", response_model=List[PhotoResponse], status_code=status.HTTP_201_CREATED)
async def upload_photos(
    request: Request,
    customer_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(Customer.id == customer_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Customer.created_by_employee_id == current_user.id)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if len(files) > settings.max_upload_files_per_request:
        raise HTTPException(
            status_code=400,
            detail=f"Upload up to {settings.max_upload_files_per_request} photos at once. Larger uploads are sent in batches.",
        )

    storage = get_storage()
    uploaded: list[PhotoResponse] = []
    for file in files:
        content = await file.read()
        mime = validate_image(content)
        # Store the exact uploaded bytes. Do not resize, recompress, or change image quality.
        path = await storage.save(content, file.filename or "photo.jpg", mime)
        photo = Photo(
            customer_id=customer_id,
            uploaded_by_employee_id=current_user.id,
            file_name=file.filename or "photo.jpg",
            file_path=path,
            file_size=len(content),
            mime_type=mime,
        )
        db.add(photo)
        await db.flush()
        resp = PhotoResponse.model_validate(photo)
        resp.url = storage.get_url(path)
        uploaded.append(resp)
        await log_action(
            db,
            user_id=current_user.id,
            action="upload_photo",
            entity_type="photo",
            entity_id=photo.id,
            ip_address=request.client.host if request.client else None,
        )
    return uploaded


@router.post("/cleanup-expired", response_model=MessageResponse)
async def cleanup_expired(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    deleted = await cleanup_expired_photos(db)
    return MessageResponse(message=f"Deleted {deleted} expired photo files. Customer info remains unchanged.")


@router.get("/files/{file_path:path}")
async def serve_file(file_path: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Photo).where(Photo.file_path == file_path))
    photo = result.scalar_one_or_none()
    storage = get_storage()
    try:
        content = await storage.read(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=content, media_type=photo.mime_type if photo else "application/octet-stream")


@router.delete("/{photo_id}", response_model=MessageResponse)
async def delete_photo(
    photo_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Photo).where(Photo.id == photo_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        stmt = stmt.where(Photo.uploaded_by_employee_id == current_user.id)
    result = await db.execute(stmt)
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    storage = get_storage()
    await storage.delete(photo.file_path)
    await db.delete(photo)
    await log_action(
        db,
        user_id=current_user.id,
        action="delete_photo",
        entity_type="photo",
        entity_id=photo_id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Photo deleted")
