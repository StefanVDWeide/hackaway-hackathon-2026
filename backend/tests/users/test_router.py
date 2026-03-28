"""Tests for user router endpoints."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.common.db import get_session
from app.common.models import Base, User, Wallet
from app.main import app
from app.modules.users.service import create_access_token, hash_password


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite engine and session for router tests."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    """ASGI test client with session dependency override."""

    async def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(db_session: AsyncSession) -> User:
    """Insert a user directly so we can test login/me without hitting register."""
    user = User(
        email="fixture@example.com",
        hashed_password=hash_password("testpass"),
        display_name="Fixture User",
    )
    db_session.add(user)
    await db_session.flush()
    wallet = Wallet(user_id=user.id)
    db_session.add(wallet)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(registered_user: User) -> dict:
    token = create_access_token(registered_user.id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /users/register
# ---------------------------------------------------------------------------


async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/users/register",
        json={
            "email": "new@example.com",
            "password": "secret",
            "display_name": "New User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert body["display_name"] == "New User"
    assert "id" in body
    assert "hashed_password" not in body


async def test_register_duplicate_email(
    client: AsyncClient, registered_user: User
):
    resp = await client.post(
        "/users/register",
        json={
            "email": "fixture@example.com",
            "password": "secret",
            "display_name": "Dup",
        },
    )
    assert resp.status_code == 409


async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post(
        "/users/register",
        json={"email": "not-an-email", "password": "s", "display_name": "X"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /users/login
# ---------------------------------------------------------------------------


async def test_login_success(client: AsyncClient, registered_user: User):
    resp = await client.post(
        "/users/login",
        json={"email": "fixture@example.com", "password": "testpass"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, registered_user: User):
    resp = await client.post(
        "/users/login",
        json={"email": "fixture@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post(
        "/users/login",
        json={"email": "ghost@example.com", "password": "x"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------


async def test_me_success(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "fixture@example.com"


async def test_me_no_token(client: AsyncClient):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


async def test_me_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/users/me", headers={"Authorization": "Bearer bad.token.here"}
    )
    assert resp.status_code == 401
