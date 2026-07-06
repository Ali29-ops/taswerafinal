"""Photo print pricing helpers."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.print_settings import PrintSettings

DEFAULT_PRICE_EGP = 120.0
SETTINGS_ROW_ID = 1


def calculate_sale_amount(photo_count: int, price_per_photo: float) -> float:
    return round(photo_count * price_per_photo, 2)


async def get_print_price(db: AsyncSession, branch_id: int | None = None) -> float:
    if branch_id is not None:
        from app.services.branches import get_branch_price

        return await get_branch_price(db, branch_id)

    result = await db.execute(select(PrintSettings).where(PrintSettings.id == SETTINGS_ROW_ID))
    settings = result.scalar_one_or_none()
    if not settings:
        return DEFAULT_PRICE_EGP
    return settings.price_per_photo


async def get_or_create_print_settings(db: AsyncSession) -> PrintSettings:
    result = await db.execute(select(PrintSettings).where(PrintSettings.id == SETTINGS_ROW_ID))
    settings = result.scalar_one_or_none()
    if settings:
        return settings
    settings = PrintSettings(id=SETTINGS_ROW_ID, price_per_photo=DEFAULT_PRICE_EGP)
    db.add(settings)
    await db.flush()
    return settings


async def update_print_price(db: AsyncSession, price: float, updated_by_id: int) -> PrintSettings:
    settings = await get_or_create_print_settings(db)
    settings.price_per_photo = price
    settings.updated_by_id = updated_by_id
    return settings
