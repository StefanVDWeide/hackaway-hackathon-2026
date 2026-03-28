"""Tests for listings router endpoints (OpenAI embedding calls are mocked)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.common.db import get_session
from app.common.models import Base, Category, Listing, User, Wallet
from app.common.types.listings import Condition, ListingStatus
from app.main import app
from app.modules.users.service import create_access_token, hash_password

FAKE_EMBEDDING = [0.1] * 1536


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
async def seller(db_session: AsyncSession) -> User:
    user = User(
        email="seller@example.com",
        hashed_password=hash_password("pass"),
        display_name="Seller",
        latitude=52.37,
        longitude=4.89,
    )
    db_session.add(user)
    await db_session.flush()
    wallet = Wallet(user_id=user.id)
    db_session.add(wallet)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def seller_headers(seller: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(seller.id)}"}


@pytest.fixture(autouse=True)
def mock_embedding():
    with patch(
        "app.modules.listings.service.generate_embedding",
        new_callable=AsyncMock,
        return_value=FAKE_EMBEDDING,
    ):
        yield


# ---------------------------------------------------------------------------
# POST /listings/
# ---------------------------------------------------------------------------


async def test_create_listing(client: AsyncClient, seller_headers: dict):
    resp = await client.post(
        "/listings/",
        json={
            "title": "Cool Keyboard",
            "description": "Mechanical, cherry MX blue",
            "price": 150,
            "condition": "new",
        },
        headers=seller_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Cool Keyboard"
    assert body["status"] == "draft"
    assert body["seller_display_name"] == "Seller"


async def test_create_listing_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/listings/",
        json={
            "title": "X",
            "description": "Y",
            "price": 10,
            "condition": "new",
        },
    )
    assert resp.status_code == 401


async def test_create_listing_validation(
    client: AsyncClient, seller_headers: dict
):
    resp = await client.post(
        "/listings/",
        json={
            "title": "X",
            "description": "Y",
            "price": -5,  # invalid
            "condition": "new",
        },
        headers=seller_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /listings/{id}
# ---------------------------------------------------------------------------


async def test_get_listing(client: AsyncClient, seller_headers: dict):
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Item",
            "description": "Desc",
            "price": 100,
            "condition": "good",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]

    resp = await client.get(f"/listings/{listing_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Item"


async def test_get_listing_not_found(client: AsyncClient):
    resp = await client.get(f"/listings/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /listings/{id}
# ---------------------------------------------------------------------------


async def test_update_listing(client: AsyncClient, seller_headers: dict):
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Old",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/listings/{listing_id}",
        json={"title": "Updated"},
        headers=seller_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


async def test_update_listing_not_owner(
    client: AsyncClient, seller_headers: dict, db_session: AsyncSession
):
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Mine",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]

    # Create another user
    other = User(
        email="other@example.com",
        hashed_password=hash_password("pass"),
        display_name="Other",
    )
    db_session.add(other)
    await db_session.flush()
    other_headers = {
        "Authorization": f"Bearer {create_access_token(other.id)}"
    }

    resp = await client.patch(
        f"/listings/{listing_id}",
        json={"title": "Hacked"},
        headers=other_headers,
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /listings/{id}/publish & /archive
# ---------------------------------------------------------------------------


async def test_publish_and_archive(
    client: AsyncClient, seller_headers: dict
):
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Item",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]

    # Publish
    resp = await client.post(
        f"/listings/{listing_id}/publish", headers=seller_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    # Archive
    resp = await client.post(
        f"/listings/{listing_id}/archive", headers=seller_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "archived"


async def test_publish_already_active(
    client: AsyncClient, seller_headers: dict
):
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Item",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]
    await client.post(
        f"/listings/{listing_id}/publish", headers=seller_headers
    )

    resp = await client.post(
        f"/listings/{listing_id}/publish", headers=seller_headers
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /listings/{id}
# ---------------------------------------------------------------------------


async def test_delete_draft_listing(
    client: AsyncClient, seller_headers: dict
):
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Draft",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/listings/{listing_id}", headers=seller_headers
    )
    assert resp.status_code == 204


async def test_delete_active_listing_fails(
    client: AsyncClient, seller_headers: dict
):
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Active",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]
    await client.post(
        f"/listings/{listing_id}/publish", headers=seller_headers
    )

    resp = await client.delete(
        f"/listings/{listing_id}", headers=seller_headers
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /listings/ (browse)
# ---------------------------------------------------------------------------


async def test_browse_listings(client: AsyncClient, seller_headers: dict):
    # Create and publish a listing
    create_resp = await client.post(
        "/listings/",
        json={
            "title": "Browsable",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    listing_id = create_resp.json()["id"]
    await client.post(
        f"/listings/{listing_id}/publish", headers=seller_headers
    )

    resp = await client.get("/listings/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_browse_excludes_drafts(
    client: AsyncClient, seller_headers: dict
):
    await client.post(
        "/listings/",
        json={
            "title": "Draft",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    resp = await client.get("/listings/")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# ---------------------------------------------------------------------------
# GET /listings/me
# ---------------------------------------------------------------------------


async def test_my_listings(client: AsyncClient, seller_headers: dict):
    await client.post(
        "/listings/",
        json={
            "title": "My Item",
            "description": "Desc",
            "price": 100,
            "condition": "new",
        },
        headers=seller_headers,
    )
    resp = await client.get("/listings/me", headers=seller_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "My Item"
