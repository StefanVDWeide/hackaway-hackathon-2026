import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.listing import Category
from app.modules.categories.schemas import CategoryCreate


async def create_category(session: AsyncSession, data: CategoryCreate) -> Category:
    """Create a new category. Raises ValueError if slug already exists."""
    existing = await session.execute(
        select(Category).where(Category.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Category with slug '{data.slug}' already exists")

    category = Category(**data.model_dump())
    session.add(category)
    await session.flush()
    await session.refresh(category)
    return category


async def get_all_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def get_category(session: AsyncSession, category_id: uuid.UUID) -> Category | None:
    return await session.get(Category, category_id)
