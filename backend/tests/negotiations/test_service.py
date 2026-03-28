"""Tests for negotiation service — bids, counter-offers, conversations."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.listing import Listing
from app.common.models.negotiation import Bid, Conversation, Message
from app.common.models.user import User
from app.common.types.listings import Condition, ListingStatus
from app.common.types.negotiations import BidStatus, BidType
from app.common.types.transactions import TransactionStatus
from app.modules.negotiations.schemas import BidCreate, CounterBidCreate, MessageCreate
from app.modules.negotiations.service import (
    accept_bid,
    counter_bid,
    get_bid,
    get_conversation,
    list_bids_for_listing,
    list_conversations,
    list_my_bids,
    place_bid,
    reject_bid,
    send_message,
)

pytest_plugins = ["tests.domain_conftest"]


def _bid_data(listing_id: uuid.UUID) -> BidCreate:
    return BidCreate(
        listing_id=listing_id,
        amount=200,
    )


# ---------------------------------------------------------------------------
# place_bid
# ---------------------------------------------------------------------------


async def test_place_bid(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    assert bid.amount == 200
    assert bid.status == BidStatus.PENDING
    assert bid.bid_type == BidType.BUYER
    assert bid.bidder_id == sample_buyer.id


async def test_place_bid_creates_conversation_and_message(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    result = await session.execute(
        select(Conversation).where(
            Conversation.listing_id == sample_listing.id,
            Conversation.buyer_id == sample_buyer.id,
        )
    )
    conv = result.scalar_one()
    assert conv is not None

    msgs = await session.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )
    msg = msgs.scalar_one()
    assert msg.bid_id is not None
    assert "200" in msg.body


async def test_place_bid_on_inactive_listing(
    session: AsyncSession, sample_user: User, sample_buyer: User
):
    listing = Listing(
        seller_id=sample_user.id,
        title="Draft",
        description="d",
        price=100,
        condition=Condition.NEW,
        status=ListingStatus.DRAFT,
    )
    session.add(listing)
    await session.flush()

    with pytest.raises(ValueError, match="not active"):
        await place_bid(session, sample_buyer.id, _bid_data(listing.id))


async def test_place_bid_on_own_listing(
    session: AsyncSession, sample_listing: Listing, sample_user: User
):
    with pytest.raises(ValueError, match="own listing"):
        await place_bid(session, sample_user.id, _bid_data(sample_listing.id))


async def test_place_bid_duplicate_pending(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    with pytest.raises(ValueError, match="already have a pending bid"):
        await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))


async def test_place_bid_on_nonexistent_listing(
    session: AsyncSession, sample_buyer: User
):
    with pytest.raises(ValueError, match="Listing not found"):
        await place_bid(session, sample_buyer.id, _bid_data(uuid.uuid4()))


# ---------------------------------------------------------------------------
# counter_bid
# ---------------------------------------------------------------------------


async def test_seller_counters_buyer_bid(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    counter_data = CounterBidCreate(amount=180)
    counter = await counter_bid(session, sample_user.id, bid.id, counter_data)

    assert counter.amount == 180
    assert counter.bid_type == BidType.SELLER
    assert counter.parent_bid_id == bid.id
    assert counter.status == BidStatus.PENDING

    # Original bid should be COUNTERED
    await session.refresh(bid)
    assert bid.status == BidStatus.COUNTERED


async def test_buyer_counters_seller_bid(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    seller_counter = await counter_bid(
        session,
        sample_user.id,
        bid.id,
        CounterBidCreate(amount=180),
    )

    buyer_counter = await counter_bid(
        session,
        sample_buyer.id,
        seller_counter.id,
        CounterBidCreate(amount=190),
    )
    assert buyer_counter.bid_type == BidType.BUYER
    assert buyer_counter.parent_bid_id == seller_counter.id


async def test_counter_non_pending_bid_fails(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    await reject_bid(session, sample_user.id, bid.id)

    with pytest.raises(ValueError, match="pending"):
        await counter_bid(session, sample_user.id, bid.id, CounterBidCreate(amount=100))


async def test_counter_own_bid_type_fails(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    """Buyer cannot counter their own BUYER bid."""
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    with pytest.raises(ValueError, match="counter seller bids"):
        await counter_bid(
            session, sample_buyer.id, bid.id, CounterBidCreate(amount=100)
        )


async def test_counter_by_unrelated_user_fails(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    stranger = User(
        email="stranger@example.com", hashed_password="x", display_name="Stranger"
    )
    session.add(stranger)
    await session.flush()

    with pytest.raises(PermissionError, match="participant"):
        await counter_bid(session, stranger.id, bid.id, CounterBidCreate(amount=100))


# ---------------------------------------------------------------------------
# accept_bid
# ---------------------------------------------------------------------------


async def test_accept_bid_creates_transaction(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    txn = await accept_bid(session, sample_user.id, bid.id)

    assert txn.amount == 200
    assert txn.buyer_id == sample_buyer.id
    assert txn.seller_id == sample_user.id
    assert txn.status == TransactionStatus.PENDING_ESCROW

    await session.refresh(bid)
    assert bid.status == BidStatus.ACCEPTED

    await session.refresh(sample_listing)
    assert sample_listing.status == ListingStatus.SOLD


async def test_accept_bid_rejects_others(
    session: AsyncSession, sample_listing: Listing, sample_user: User
):
    buyer1 = User(email="b1@example.com", hashed_password="x", display_name="B1")
    buyer2 = User(email="b2@example.com", hashed_password="x", display_name="B2")
    session.add_all([buyer1, buyer2])
    await session.flush()

    bid1 = await place_bid(session, buyer1.id, _bid_data(sample_listing.id))
    data2 = _bid_data(sample_listing.id)
    data2.amount = 300
    bid2 = await place_bid(session, buyer2.id, data2)

    await accept_bid(session, sample_user.id, bid1.id)

    await session.refresh(bid2)
    assert bid2.status == BidStatus.REJECTED


async def test_accept_counter_offer(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    """Buyer accepts a seller counter-offer."""
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    counter = await counter_bid(
        session,
        sample_user.id,
        bid.id,
        CounterBidCreate(amount=180),
    )

    txn = await accept_bid(session, sample_buyer.id, counter.id)
    assert txn.amount == 180
    assert txn.buyer_id == sample_buyer.id  # original buyer, not counter bidder


async def test_accept_own_bid_fails(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    with pytest.raises(PermissionError):
        await accept_bid(session, sample_buyer.id, bid.id)


async def test_accept_already_accepted_fails(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    await accept_bid(session, sample_user.id, bid.id)

    with pytest.raises(ValueError, match="pending"):
        await accept_bid(session, sample_user.id, bid.id)


# ---------------------------------------------------------------------------
# reject_bid
# ---------------------------------------------------------------------------


async def test_reject_bid(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    rejected = await reject_bid(session, sample_user.id, bid.id)
    assert rejected.status == BidStatus.REJECTED


async def test_reject_own_bid_fails(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    with pytest.raises(PermissionError):
        await reject_bid(session, sample_buyer.id, bid.id)


# ---------------------------------------------------------------------------
# Conversations & messages
# ---------------------------------------------------------------------------


async def test_send_message(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    # Place a bid to create the conversation
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    result = await session.execute(
        select(Conversation).where(Conversation.buyer_id == sample_buyer.id)
    )
    conv = result.scalar_one()

    msg = await send_message(
        session, sample_buyer.id, conv.id, MessageCreate(body="Hello seller!")
    )
    assert msg.body == "Hello seller!"
    assert msg.sender_id == sample_buyer.id


async def test_send_message_seller(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    result = await session.execute(
        select(Conversation).where(Conversation.buyer_id == sample_buyer.id)
    )
    conv = result.scalar_one()

    msg = await send_message(
        session, sample_user.id, conv.id, MessageCreate(body="Thanks for your bid!")
    )
    assert msg.sender_id == sample_user.id


async def test_send_message_stranger_fails(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    result = await session.execute(
        select(Conversation).where(Conversation.buyer_id == sample_buyer.id)
    )
    conv = result.scalar_one()

    stranger = User(
        email="stranger@example.com", hashed_password="x", display_name="Stranger"
    )
    session.add(stranger)
    await session.flush()

    with pytest.raises(PermissionError, match="participant"):
        await send_message(session, stranger.id, conv.id, MessageCreate(body="Hi!"))


async def test_list_conversations(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    # Buyer sees their conversation
    buyer_convos = await list_conversations(session, sample_buyer.id)
    assert len(buyer_convos) == 1

    # Seller also sees it
    seller_convos = await list_conversations(session, sample_user.id)
    assert len(seller_convos) == 1


async def test_get_conversation_with_messages(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))

    result = await session.execute(
        select(Conversation).where(Conversation.buyer_id == sample_buyer.id)
    )
    conv = result.scalar_one()

    loaded = await get_conversation(session, sample_buyer.id, conv.id)
    assert len(loaded.messages) >= 1  # at least the bid message


# ---------------------------------------------------------------------------
# Listing / my bids queries
# ---------------------------------------------------------------------------


async def test_list_bids_for_listing(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    bids = await list_bids_for_listing(session, sample_user.id, sample_listing.id)
    assert len(bids) == 1


async def test_list_bids_for_listing_not_owner(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    with pytest.raises(PermissionError, match="do not own"):
        await list_bids_for_listing(session, sample_buyer.id, sample_listing.id)


async def test_list_my_bids(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    bids = await list_my_bids(session, sample_buyer.id)
    assert len(bids) == 1
    assert bids[0].bidder_id == sample_buyer.id


async def test_get_bid(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User
):
    bid = await place_bid(session, sample_buyer.id, _bid_data(sample_listing.id))
    found = await get_bid(session, bid.id)
    assert found is not None
    assert found.id == bid.id


async def test_get_bid_not_found(session: AsyncSession):
    found = await get_bid(session, uuid.uuid4())
    assert found is None
