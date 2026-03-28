"""Tests for Listing and Category models."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.types.listings import Condition, ListingStatus
from app.modules.listings.models import Category, Listing

pytest_plugins = ["tests.domain_conftest"]


async def test_listing_creation(session: AsyncSession, sample_listing: Listing) -> None:
    assert isinstance(sample_listing.id, uuid.UUID)
    assert sample_listing.title == "Vintage Keyboard"
    assert sample_listing.price == 250
    assert sample_listing.condition == Condition.GOOD
    assert sample_listing.status == ListingStatus.ACTIVE


async def test_listing_default_status(session: AsyncSession, sample_user) -> None:
    listing = Listing(
        seller_id=sample_user.id,
        title="Test",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    session.add(listing)
    await session.flush()
    assert listing.status == ListingStatus.DRAFT


async def test_category_hierarchy(session: AsyncSession) -> None:
    parent = Category(name="Electronics", slug="electronics")
    session.add(parent)
    await session.flush()

    child = Category(name="Phones", slug="phones", parent_id=parent.id)
    session.add(child)
    await session.flush()

    result = await session.execute(
        select(Category).where(Category.parent_id == parent.id),
    )
    children = list(result.scalars().all())
    assert len(children) == 1
    assert children[0].slug == "phones"


async def test_listing_category_association(
    session: AsyncSession, sample_listing: Listing,
) -> None:
    cat = Category(name="Keyboards", slug="keyboards")
    session.add(cat)
    await session.flush()

    # Use raw SQL insert into association table to avoid lazy-load in async
    from app.modules.listings.models import listing_categories
    await session.execute(
        listing_categories.insert().values(
            listing_id=sample_listing.id, category_id=cat.id,
        ),
    )
    await session.flush()

    result = await session.execute(
        select(Listing)
        .where(Listing.id == sample_listing.id)
        .options(selectinload(Listing.categories)),
    )
    listing = result.scalar_one()
    assert len(listing.categories) == 1
    assert listing.categories[0].slug == "keyboards"
