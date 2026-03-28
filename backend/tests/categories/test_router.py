"""Tests for category router endpoints."""

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
    async def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(db_session: AsyncSession) -> dict:
    user = User(
        email="cat-admin@example.com",
        hashed_password=hash_password("pass"),
        display_name="Admin",
    )
    db_session.add(user)
    await db_session.flush()
    wallet = Wallet(user_id=user.id)
    db_session.add(wallet)
    await db_session.flush()
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /categories/
# ---------------------------------------------------------------------------


async def test_create_category(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/categories/",
        json={"name": "Books", "slug": "books"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Books"
    assert body["slug"] == "books"


async def test_create_category_duplicate_slug(
    client: AsyncClient, auth_headers: dict
):
    await client.post(
        "/categories/",
        json={"name": "Books", "slug": "books"},
        headers=auth_headers,
    )
    resp = await client.post(
        "/categories/",
        json={"name": "Other Books", "slug": "books"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_create_category_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/categories/", json={"name": "Books", "slug": "books"}
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /categories/
# ---------------------------------------------------------------------------


async def test_list_categories_empty(client: AsyncClient):
    resp = await client.get("/categories/")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_categories(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/categories/",
        json={"name": "Zebra", "slug": "zebra"},
        headers=auth_headers,
    )
    await client.post(
        "/categories/",
        json={"name": "Apple", "slug": "apple"},
        headers=auth_headers,
    )
    resp = await client.get("/categories/")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert names == ["Apple", "Zebra"]


# ---------------------------------------------------------------------------
# GET /categories/{id}
# ---------------------------------------------------------------------------


async def test_get_category(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/categories/",
        json={"name": "Music", "slug": "music"},
        headers=auth_headers,
    )
    cat_id = create_resp.json()["id"]
    resp = await client.get(f"/categories/{cat_id}")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "music"


async def test_get_category_not_found(client: AsyncClient):
    import uuid

    resp = await client.get(f"/categories/{uuid.uuid4()}")
    assert resp.status_code == 404
