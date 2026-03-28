"""Tests for user service functions."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.user import User, Wallet
from app.modules.users.schemas import UserRegister
from app.modules.users.service import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    register_user,
    verify_password,
)

pytest_plugins = ["tests.domain_conftest"]


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("secret123")
    assert hashed.startswith("$2b$")
    assert hashed != "secret123"


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrong", hashed) is False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------


def test_create_and_decode_access_token():
    uid = uuid.uuid4()
    token = create_access_token(uid)
    decoded = decode_access_token(token)
    assert decoded == uid


def test_decode_access_token_invalid():
    import jwt as pyjwt

    with pytest.raises(pyjwt.PyJWTError):
        decode_access_token("invalid.token.here")


# ---------------------------------------------------------------------------
# User queries
# ---------------------------------------------------------------------------


async def test_get_user_by_email_found(session: AsyncSession, sample_user: User):
    found = await get_user_by_email(session, "alice@example.com")
    assert found is not None
    assert found.id == sample_user.id


async def test_get_user_by_email_not_found(session: AsyncSession):
    found = await get_user_by_email(session, "nobody@example.com")
    assert found is None


async def test_get_user_by_id_found(session: AsyncSession, sample_user: User):
    found = await get_user_by_id(session, sample_user.id)
    assert found is not None
    assert found.email == sample_user.email


async def test_get_user_by_id_not_found(session: AsyncSession):
    found = await get_user_by_id(session, uuid.uuid4())
    assert found is None


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def test_register_user_creates_user_and_wallet(session: AsyncSession):
    data = UserRegister(
        email="new@example.com",
        password="pass123",
        display_name="New User",
        latitude=51.0,
        longitude=4.0,
    )
    user = await register_user(session, data)
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "new@example.com"
    assert user.display_name == "New User"

    # Wallet should have been created
    wallet = await session.get(Wallet, user.id)
    # Wallet is linked by user_id, query it
    from sqlalchemy import select

    result = await session.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = result.scalar_one()
    assert wallet.balance == 0


async def test_register_user_duplicate_email(session: AsyncSession, sample_user: User):
    data = UserRegister(
        email="alice@example.com",
        password="pass",
        display_name="Dup",
    )
    with pytest.raises(ValueError, match="Email already registered"):
        await register_user(session, data)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_authenticate_user_success(session: AsyncSession):
    # Register first so we know the password
    data = UserRegister(
        email="auth@example.com", password="correcthorse", display_name="Auth"
    )
    user = await register_user(session, data)

    authed = await authenticate_user(session, "auth@example.com", "correcthorse")
    assert authed.id == user.id


async def test_authenticate_user_wrong_password(session: AsyncSession):
    data = UserRegister(
        email="auth2@example.com", password="correcthorse", display_name="Auth2"
    )
    await register_user(session, data)

    with pytest.raises(ValueError, match="Invalid email or password"):
        await authenticate_user(session, "auth2@example.com", "wrongpassword")


async def test_authenticate_user_unknown_email(session: AsyncSession):
    with pytest.raises(ValueError, match="Invalid email or password"):
        await authenticate_user(session, "ghost@example.com", "pass")


async def test_authenticate_user_inactive(session: AsyncSession):
    data = UserRegister(
        email="inactive@example.com", password="pass", display_name="Inactive"
    )
    user = await register_user(session, data)
    user.is_active = False
    await session.flush()

    with pytest.raises(ValueError, match="User account is inactive"):
        await authenticate_user(session, "inactive@example.com", "pass")
