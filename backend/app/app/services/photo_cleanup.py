"""Automatic cleanup for uploaded photo files."""

import asyncio
import contextlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.photo import Photo
from app.services.storage import get_storage

settings = get_settings()


async def cleanup_expired_photos(db: AsyncSession) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.photo_retention_days)
    result = await db.execute(select(Photo).where(Photo.created_at < cutoff).order_by(Photo.created_at.asc()))
    photos = result.scalars().all()
    storage = get_storage()
    deleted = 0
    for photo in photos:
        with contextlib.suppress(Exception):
            await storage.delete(photo.file_path)
        await db.delete(photo)
        deleted += 1
    await db.commit()
    return deleted


async def photo_cleanup_loop() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await cleanup_expired_photos(db)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        await asyncio.sleep(settings.photo_cleanup_interval_minutes * 60)
