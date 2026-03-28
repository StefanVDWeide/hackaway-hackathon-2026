"""Tests for base model primitives."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import Widget


async def test_model_has_uuid_pk(session: AsyncSession) -> None:
    widget = Widget(name="bolt", color="silver")
    session.add(widget)
    await session.flush()

    assert isinstance(widget.id, uuid.UUID)


async def test_model_timestamps_populated(session: AsyncSession) -> None:
    widget = Widget(name="gear", color="brass")
    session.add(widget)
    await session.flush()
    await session.refresh(widget)

    assert isinstance(widget.created_at, datetime)
    assert isinstance(widget.updated_at, datetime)


async def test_model_persists_and_queries(session: AsyncSession) -> None:
    widget = Widget(name="spring", color="steel")
    session.add(widget)
    await session.flush()

    result = await session.execute(select(Widget).where(Widget.name == "spring"))
    fetched = result.scalar_one()

    assert fetched.id == widget.id
    assert fetched.color == "steel"
