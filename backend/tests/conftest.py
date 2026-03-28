"""Shared test fixtures — async SQLite engine + session."""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from pydantic import ConfigDict
from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Mapped, mapped_column

import pytest

from app.common.models.base import Base, TimestampMixin
from app.common.repos.base import BaseRepository
from app.common.schemas.base import BaseSchema, CreateSchema, ReadSchema, UpdateSchema


# ---------------------------------------------------------------------------
# Fake "Widget" domain used across tests
# ---------------------------------------------------------------------------


class Widget(TimestampMixin, Base):
    __tablename__ = "widgets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)


class WidgetCreate(CreateSchema):
    name: str
    color: str


class WidgetUpdate(UpdateSchema):
    name: str | None = None
    color: str | None = None


class WidgetRead(ReadSchema):
    name: str
    color: str


class WidgetRepository(BaseRepository[Widget, WidgetCreate, WidgetUpdate]):
    model = Widget


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def engine():
    """Create an in-memory async SQLite engine for each test."""
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine) -> AsyncGenerator[AsyncSession]:
    """Provide a transactional async session that rolls back after each test."""
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def widget_repo(session: AsyncSession) -> WidgetRepository:
    return WidgetRepository(session)
