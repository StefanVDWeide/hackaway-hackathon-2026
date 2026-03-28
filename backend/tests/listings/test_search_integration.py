"""Integration test for /listings/search — hits real PostgreSQL + OpenAI."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.db import get_session
from app.common.models import Base, User, Wallet, Listing
from app.common.types.listings import Condition, ListingStatus
from app.config import settings
from app.main import app
from app.modules.users.service import create_access_token, hash_password


@pytest.fixture
async def pg_session():
    """Session backed by the real PostgreSQL database."""
    engine = create_async_engine(settings.database_url, echo=True)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def pg_client(pg_session: AsyncSession):
    async def override():
        yield pg_session

    app.dependency_overrides[get_session] = override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_search_returns_results(pg_client: AsyncClient):
    """Search the seeded data for 'leather jacket'."""
    resp = await pg_client.get("/listings/search", params={"query": "leather jacket"})
    assert resp.status_code == 200, f"Search failed: {resp.status_code} {resp.text}"
    results = resp.json()
    assert isinstance(results, list)
    # Seeded data includes "Vintage Leather Jacket"
    titles = [r["listing"]["title"] for r in results]
    assert any("leather" in t.lower() for t in titles), f"Expected leather jacket in {titles}"


async def test_search_blue_vest(pg_client: AsyncClient):
    """Search for 'blue vest' — semantic search should return results even without exact match."""
    resp = await pg_client.get("/listings/search", params={"query": "blue vest"})
    assert resp.status_code == 200, f"Search failed: {resp.status_code} {resp.text}"
    results = resp.json()
    assert isinstance(results, list)
    # Semantic search should return clothing-adjacent results (e.g. leather jacket)
    assert len(results) > 0, "Semantic search should return results even for non-exact queries"
