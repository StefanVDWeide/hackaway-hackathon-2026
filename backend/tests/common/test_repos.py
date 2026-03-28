"""Tests for the base repository CRUD operations."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import Widget, WidgetCreate, WidgetRepository, WidgetUpdate


async def test_create(widget_repo: WidgetRepository) -> None:
    widget = await widget_repo.create(WidgetCreate(name="bolt", color="silver"))

    assert isinstance(widget.id, uuid.UUID)
    assert widget.name == "bolt"
    assert widget.color == "silver"


async def test_get_by_id(widget_repo: WidgetRepository) -> None:
    created = await widget_repo.create(WidgetCreate(name="gear", color="brass"))
    fetched = await widget_repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "gear"


async def test_get_by_id_not_found(widget_repo: WidgetRepository) -> None:
    result = await widget_repo.get_by_id(uuid.uuid4())
    assert result is None


async def test_get_all(widget_repo: WidgetRepository) -> None:
    await widget_repo.create(WidgetCreate(name="a", color="red"))
    await widget_repo.create(WidgetCreate(name="b", color="blue"))
    await widget_repo.create(WidgetCreate(name="c", color="green"))

    all_widgets = await widget_repo.get_all()
    assert len(all_widgets) == 3


async def test_get_all_with_pagination(widget_repo: WidgetRepository) -> None:
    for i in range(5):
        await widget_repo.create(WidgetCreate(name=f"w{i}", color="grey"))

    page = await widget_repo.get_all(offset=2, limit=2)
    assert len(page) == 2


async def test_update(widget_repo: WidgetRepository) -> None:
    created = await widget_repo.create(WidgetCreate(name="bolt", color="silver"))
    updated = await widget_repo.update(created.id, WidgetUpdate(color="gold"))

    assert updated is not None
    assert updated.color == "gold"
    assert updated.name == "bolt"  # unchanged


async def test_update_partial(widget_repo: WidgetRepository) -> None:
    created = await widget_repo.create(WidgetCreate(name="bolt", color="silver"))
    updated = await widget_repo.update(created.id, WidgetUpdate())

    assert updated is not None
    assert updated.name == "bolt"
    assert updated.color == "silver"


async def test_update_not_found(widget_repo: WidgetRepository) -> None:
    result = await widget_repo.update(uuid.uuid4(), WidgetUpdate(name="x"))
    assert result is None


async def test_delete(widget_repo: WidgetRepository) -> None:
    created = await widget_repo.create(WidgetCreate(name="bolt", color="silver"))
    deleted = await widget_repo.delete(created.id)

    assert deleted is True
    assert await widget_repo.get_by_id(created.id) is None


async def test_delete_not_found(widget_repo: WidgetRepository) -> None:
    result = await widget_repo.delete(uuid.uuid4())
    assert result is False
