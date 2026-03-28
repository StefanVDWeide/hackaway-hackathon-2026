"""Tests for listing service functions (OpenAI embedding calls are mocked)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.listing import Category, Listing
from app.common.models.user import User
from app.common.types.listings import Condition, ListingStatus
from app.modules.categories.schemas import CategoryCreate
from app.modules.categories.service import create_category
from app.modules.listings.schemas import (
    ListingBrowseParams,
    ListingCreate,
    ListingUpdate,
)
from app.modules.listings.service import (
    _reciprocal_rank_fusion,
    archive_listing,
    browse_listings,
    create_listing,
    delete_listing,
    get_listing,
    get_my_listings,
    publish_listing,
    update_listing,
)

pytest_plugins = ["tests.domain_conftest"]

FAKE_EMBEDDING = [0.1] * 1536


@pytest.fixture(autouse=True)
def mock_embedding():
    """Mock OpenAI embedding calls for all tests in this module."""
    with patch(
        "app.modules.listings.service.generate_embedding",
        new_callable=AsyncMock,
        return_value=FAKE_EMBEDDING,
    ) as m:
        yield m


# ---------------------------------------------------------------------------
# create_listing
# ---------------------------------------------------------------------------


async def test_create_listing(session: AsyncSession, sample_user: User):
    data = ListingCreate(
        title="Test Item",
        description="A great item",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    assert listing.title == "Test Item"
    assert listing.status == ListingStatus.DRAFT
    assert listing.seller_id == sample_user.id
    assert isinstance(listing.id, uuid.UUID)


async def test_create_listing_with_categories(
    session: AsyncSession, sample_user: User
):
    cat = await create_category(
        session, CategoryCreate(name="Tech", slug="tech")
    )
    data = ListingCreate(
        title="Gadget",
        description="Cool gadget",
        price=50,
        condition=Condition.LIKE_NEW,
        category_ids=[cat.id],
    )
    listing = await create_listing(session, sample_user.id, data)
    assert len(listing.categories) == 1
    assert listing.categories[0].slug == "tech"


async def test_create_listing_generates_embedding(
    session: AsyncSession, sample_user: User, mock_embedding: AsyncMock
):
    data = ListingCreate(
        title="Keyboard",
        description="Mechanical",
        price=200,
        condition=Condition.GOOD,
    )
    await create_listing(session, sample_user.id, data)
    mock_embedding.assert_called_once_with("Keyboard\nMechanical")


# ---------------------------------------------------------------------------
# update_listing
# ---------------------------------------------------------------------------


async def test_update_listing_fields(
    session: AsyncSession, sample_user: User
):
    data = ListingCreate(
        title="Old Title",
        description="Old Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)

    update = ListingUpdate(title="New Title", price=200)
    updated = await update_listing(session, listing.id, sample_user.id, update)
    assert updated.title == "New Title"
    assert updated.price == 200
    assert updated.description == "Old Desc"  # unchanged


async def test_update_listing_regenerates_embedding_on_title_change(
    session: AsyncSession, sample_user: User, mock_embedding: AsyncMock
):
    data = ListingCreate(
        title="Original",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    mock_embedding.reset_mock()

    update = ListingUpdate(title="Changed")
    await update_listing(session, listing.id, sample_user.id, update)
    mock_embedding.assert_called_once()


async def test_update_listing_no_embedding_regen_for_price_change(
    session: AsyncSession, sample_user: User, mock_embedding: AsyncMock
):
    data = ListingCreate(
        title="Item",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    mock_embedding.reset_mock()

    update = ListingUpdate(price=999)
    await update_listing(session, listing.id, sample_user.id, update)
    mock_embedding.assert_not_called()


async def test_update_listing_categories(
    session: AsyncSession, sample_user: User
):
    cat1 = await create_category(
        session, CategoryCreate(name="A", slug="a")
    )
    cat2 = await create_category(
        session, CategoryCreate(name="B", slug="b")
    )
    data = ListingCreate(
        title="Item",
        description="Desc",
        price=100,
        condition=Condition.NEW,
        category_ids=[cat1.id],
    )
    listing = await create_listing(session, sample_user.id, data)
    assert len(listing.categories) == 1

    update = ListingUpdate(category_ids=[cat2.id])
    updated = await update_listing(session, listing.id, sample_user.id, update)
    assert len(updated.categories) == 1
    assert updated.categories[0].slug == "b"


async def test_update_listing_not_found(
    session: AsyncSession, sample_user: User
):
    update = ListingUpdate(title="X")
    with pytest.raises(ValueError, match="Listing not found"):
        await update_listing(session, uuid.uuid4(), sample_user.id, update)


async def test_update_listing_not_owner(
    session: AsyncSession, sample_user: User, sample_buyer: User
):
    data = ListingCreate(
        title="Item",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)

    update = ListingUpdate(title="Hacked")
    with pytest.raises(PermissionError, match="do not own"):
        await update_listing(session, listing.id, sample_buyer.id, update)


# ---------------------------------------------------------------------------
# delete_listing
# ---------------------------------------------------------------------------


async def test_delete_draft_listing(
    session: AsyncSession, sample_user: User
):
    data = ListingCreate(
        title="Draft",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    assert listing.status == ListingStatus.DRAFT

    await delete_listing(session, listing.id, sample_user.id)
    assert await get_listing(session, listing.id) is None


async def test_delete_active_listing_fails(
    session: AsyncSession, sample_user: User
):
    data = ListingCreate(
        title="Active",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    await publish_listing(session, listing.id, sample_user.id)

    with pytest.raises(ValueError, match="Only DRAFT"):
        await delete_listing(session, listing.id, sample_user.id)


async def test_delete_listing_not_owner(
    session: AsyncSession, sample_user: User, sample_buyer: User
):
    data = ListingCreate(
        title="Mine",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)

    with pytest.raises(PermissionError, match="do not own"):
        await delete_listing(session, listing.id, sample_buyer.id)


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


async def test_publish_listing(session: AsyncSession, sample_user: User):
    data = ListingCreate(
        title="Draft",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    published = await publish_listing(session, listing.id, sample_user.id)
    assert published.status == ListingStatus.ACTIVE


async def test_publish_already_active_fails(
    session: AsyncSession, sample_user: User
):
    data = ListingCreate(
        title="Item",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    await publish_listing(session, listing.id, sample_user.id)

    with pytest.raises(ValueError, match="Only DRAFT"):
        await publish_listing(session, listing.id, sample_user.id)


async def test_archive_listing(session: AsyncSession, sample_user: User):
    data = ListingCreate(
        title="Item",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    await publish_listing(session, listing.id, sample_user.id)
    archived = await archive_listing(session, listing.id, sample_user.id)
    assert archived.status == ListingStatus.ARCHIVED


async def test_archive_draft_fails(session: AsyncSession, sample_user: User):
    data = ListingCreate(
        title="Draft",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)

    with pytest.raises(ValueError, match="Only ACTIVE"):
        await archive_listing(session, listing.id, sample_user.id)


# ---------------------------------------------------------------------------
# Read / Browse
# ---------------------------------------------------------------------------


async def test_get_listing_found(session: AsyncSession, sample_user: User):
    data = ListingCreate(
        title="Findme",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    listing = await create_listing(session, sample_user.id, data)
    found = await get_listing(session, listing.id)
    assert found is not None
    assert found.title == "Findme"


async def test_get_listing_not_found(session: AsyncSession):
    found = await get_listing(session, uuid.uuid4())
    assert found is None


async def test_get_my_listings(session: AsyncSession, sample_user: User):
    for i in range(3):
        data = ListingCreate(
            title=f"Item {i}",
            description="Desc",
            price=100,
            condition=Condition.NEW,
        )
        await create_listing(session, sample_user.id, data)

    listings = await get_my_listings(session, sample_user.id)
    assert len(listings) == 3


async def test_get_my_listings_pagination(
    session: AsyncSession, sample_user: User
):
    for i in range(5):
        data = ListingCreate(
            title=f"Item {i}",
            description="Desc",
            price=100,
            condition=Condition.NEW,
        )
        await create_listing(session, sample_user.id, data)

    page = await get_my_listings(session, sample_user.id, offset=2, limit=2)
    assert len(page) == 2


async def test_get_my_listings_excludes_other_sellers(
    session: AsyncSession, sample_user: User, sample_buyer: User
):
    await create_listing(
        session,
        sample_user.id,
        ListingCreate(
            title="Mine", description="d", price=10, condition=Condition.NEW
        ),
    )
    await create_listing(
        session,
        sample_buyer.id,
        ListingCreate(
            title="Theirs", description="d", price=10, condition=Condition.NEW
        ),
    )
    mine = await get_my_listings(session, sample_user.id)
    assert len(mine) == 1
    assert mine[0].title == "Mine"


async def test_browse_listings_only_active(
    session: AsyncSession, sample_user: User
):
    # Draft listing
    await create_listing(
        session,
        sample_user.id,
        ListingCreate(
            title="Draft", description="d", price=10, condition=Condition.NEW
        ),
    )
    # Active listing
    listing = await create_listing(
        session,
        sample_user.id,
        ListingCreate(
            title="Active", description="d", price=20, condition=Condition.NEW
        ),
    )
    await publish_listing(session, listing.id, sample_user.id)

    results = await browse_listings(session, ListingBrowseParams())
    assert len(results) == 1
    assert results[0].title == "Active"


async def test_browse_listings_price_filter(
    session: AsyncSession, sample_user: User
):
    for price in [50, 100, 200]:
        l = await create_listing(
            session,
            sample_user.id,
            ListingCreate(
                title=f"P{price}",
                description="d",
                price=price,
                condition=Condition.NEW,
            ),
        )
        await publish_listing(session, l.id, sample_user.id)

    results = await browse_listings(
        session, ListingBrowseParams(min_price=80, max_price=150)
    )
    assert len(results) == 1
    assert results[0].price == 100


async def test_browse_listings_condition_filter(
    session: AsyncSession, sample_user: User
):
    for cond in [Condition.NEW, Condition.GOOD, Condition.POOR]:
        l = await create_listing(
            session,
            sample_user.id,
            ListingCreate(
                title=f"C{cond.value}",
                description="d",
                price=10,
                condition=cond,
            ),
        )
        await publish_listing(session, l.id, sample_user.id)

    results = await browse_listings(
        session, ListingBrowseParams(condition=Condition.GOOD)
    )
    assert len(results) == 1


async def test_browse_listings_category_filter(
    session: AsyncSession, sample_user: User
):
    cat = await create_category(
        session, CategoryCreate(name="Tech", slug="tech")
    )
    l1 = await create_listing(
        session,
        sample_user.id,
        ListingCreate(
            title="With Cat",
            description="d",
            price=10,
            condition=Condition.NEW,
            category_ids=[cat.id],
        ),
    )
    await publish_listing(session, l1.id, sample_user.id)

    l2 = await create_listing(
        session,
        sample_user.id,
        ListingCreate(
            title="No Cat",
            description="d",
            price=10,
            condition=Condition.NEW,
        ),
    )
    await publish_listing(session, l2.id, sample_user.id)

    results = await browse_listings(
        session, ListingBrowseParams(category_slug="tech")
    )
    assert len(results) == 1
    assert results[0].title == "With Cat"


# ---------------------------------------------------------------------------
# RRF (pure function, no DB needed)
# ---------------------------------------------------------------------------


def test_reciprocal_rank_fusion_single_list():
    """Single list: scores are 1/(k+rank)."""

    class FakeListing:
        def __init__(self, id):
            self.id = id

    a, b = FakeListing(uuid.uuid4()), FakeListing(uuid.uuid4())
    result = _reciprocal_rank_fusion([a, b], k=60)
    assert result[0][0].id == a.id
    assert result[1][0].id == b.id
    assert result[0][1] > result[1][1]


def test_reciprocal_rank_fusion_merges_lists():
    class FakeListing:
        def __init__(self, id):
            self.id = id

    shared_id = uuid.uuid4()
    a = FakeListing(shared_id)
    b = FakeListing(shared_id)
    only_ft = FakeListing(uuid.uuid4())

    result = _reciprocal_rank_fusion([a, only_ft], [b], k=60)
    # shared item should score highest (appears in both lists)
    assert result[0][0].id == shared_id
