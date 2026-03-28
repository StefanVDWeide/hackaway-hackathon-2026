"""Fixtures for domain model tests — uses all registered models."""

from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.common.models.base import Base

# Import all models so metadata is fully populated
from app.common.models import (  # noqa: F401
    Bid,
    Category,
    Conversation,
    Listing,
    Message,
    Transaction,
    User,
    Wallet,
)
from app.common.types.listings import Condition, ListingStatus
from app.common.types.negotiations import ActorType, BidStatus, BidType
from app.common.types.transactions import TransactionStatus


@pytest.fixture
async def domain_engine():
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(domain_engine) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(
        bind=domain_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def sample_user(session: AsyncSession) -> User:
    user = User(
        email="alice@example.com",
        hashed_password="fakehash",
        display_name="Alice",
        latitude=52.37,
        longitude=4.89,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


@pytest.fixture
async def sample_wallet(session: AsyncSession, sample_user: User) -> Wallet:
    wallet = Wallet(user_id=sample_user.id, balance=1000, held_balance=0)
    session.add(wallet)
    await session.flush()
    await session.refresh(wallet)
    return wallet


@pytest.fixture
async def sample_listing(session: AsyncSession, sample_user: User) -> Listing:
    listing = Listing(
        seller_id=sample_user.id,
        title="Vintage Keyboard",
        description="A beautiful mechanical keyboard from the 80s.",
        price=250,
        condition=Condition.GOOD,
        status=ListingStatus.ACTIVE,
        image_url="https://cdn.example.com/keyboard.jpg",
    )
    session.add(listing)
    await session.flush()
    await session.refresh(listing)
    return listing


@pytest.fixture
async def sample_buyer(session: AsyncSession) -> User:
    buyer = User(
        email="bob@example.com",
        hashed_password="fakehash",
        display_name="Bob",
        latitude=52.09,
        longitude=5.12,
    )
    session.add(buyer)
    await session.flush()
    await session.refresh(buyer)
    return buyer
