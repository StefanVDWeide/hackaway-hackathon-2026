"""Tests for User and Wallet models."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User, Wallet

# Pull in domain fixtures
pytest_plugins = ["tests.domain_conftest"]


async def test_user_creation(session: AsyncSession) -> None:
    user = User(
        email="test@example.com",
        hashed_password="hash123",
        display_name="Tester",
    )
    session.add(user)
    await session.flush()

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.latitude is None


async def test_user_email_unique(session: AsyncSession, sample_user: User) -> None:
    duplicate = User(
        email=sample_user.email,
        hashed_password="other",
        display_name="Dup",
    )
    session.add(duplicate)

    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await session.flush()


async def test_wallet_linked_to_user(
    session: AsyncSession, sample_user: User, sample_wallet: Wallet,
) -> None:
    result = await session.execute(
        select(Wallet).where(Wallet.user_id == sample_user.id),
    )
    wallet = result.scalar_one()
    assert wallet.balance == 1000
    assert wallet.held_balance == 0
