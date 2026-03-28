"""Tests for category service functions."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.listing import Category
from app.modules.categories.schemas import CategoryCreate
from app.modules.categories.service import (
    create_category,
    get_all_categories,
    get_category,
)

pytest_plugins = ["tests.domain_conftest"]


async def test_create_category(session: AsyncSession):
    data = CategoryCreate(name="Electronics", slug="electronics")
    cat = await create_category(session, data)
    assert cat.name == "Electronics"
    assert cat.slug == "electronics"
    assert isinstance(cat.id, uuid.UUID)


async def test_create_category_with_parent(session: AsyncSession):
    parent = CategoryCreate(name="Electronics", slug="electronics")
    parent_cat = await create_category(session, parent)

    child = CategoryCreate(name="Phones", slug="phones", parent_id=parent_cat.id)
    child_cat = await create_category(session, child)
    assert child_cat.parent_id == parent_cat.id


async def test_create_category_duplicate_slug(session: AsyncSession):
    data = CategoryCreate(name="Electronics", slug="electronics")
    await create_category(session, data)

    dup = CategoryCreate(name="Other Electronics", slug="electronics")
    with pytest.raises(ValueError, match="already exists"):
        await create_category(session, dup)


async def test_get_all_categories_empty(session: AsyncSession):
    cats = await get_all_categories(session)
    assert cats == []


async def test_get_all_categories_ordered(session: AsyncSession):
    await create_category(session, CategoryCreate(name="Zebra", slug="zebra"))
    await create_category(session, CategoryCreate(name="Apple", slug="apple"))
    cats = await get_all_categories(session)
    assert [c.name for c in cats] == ["Apple", "Zebra"]


async def test_get_category_found(session: AsyncSession):
    data = CategoryCreate(name="Books", slug="books")
    created = await create_category(session, data)
    found = await get_category(session, created.id)
    assert found is not None
    assert found.slug == "books"


async def test_get_category_not_found(session: AsyncSession):
    found = await get_category(session, uuid.uuid4())
    assert found is None
