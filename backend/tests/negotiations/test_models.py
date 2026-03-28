"""Tests for Conversation, Message, and Bid models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.types.negotiations import ActorType, BidStatus, BidType
from app.modules.negotiations.models import Bid, Conversation, Message
from app.modules.listings.models import Listing
from app.modules.users.models import User

pytest_plugins = ["tests.domain_conftest"]


async def test_conversation_creation(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User,
) -> None:
    convo = Conversation(listing_id=sample_listing.id, buyer_id=sample_buyer.id)
    session.add(convo)
    await session.flush()

    assert isinstance(convo.id, uuid.UUID)


async def test_conversation_unique_per_buyer_listing(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User,
) -> None:
    import pytest
    from sqlalchemy.exc import IntegrityError

    convo1 = Conversation(listing_id=sample_listing.id, buyer_id=sample_buyer.id)
    session.add(convo1)
    await session.flush()

    convo2 = Conversation(listing_id=sample_listing.id, buyer_id=sample_buyer.id)
    session.add(convo2)
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_message_from_user(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User,
) -> None:
    convo = Conversation(listing_id=sample_listing.id, buyer_id=sample_buyer.id)
    session.add(convo)
    await session.flush()

    msg = Message(
        conversation_id=convo.id,
        actor_type=ActorType.USER,
        sender_id=sample_buyer.id,
        body="Is this still available?",
    )
    session.add(msg)
    await session.flush()

    assert msg.actor_type == ActorType.USER
    assert msg.sender_id == sample_buyer.id


async def test_message_from_agent(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User,
) -> None:
    convo = Conversation(listing_id=sample_listing.id, buyer_id=sample_buyer.id)
    session.add(convo)
    await session.flush()

    msg = Message(
        conversation_id=convo.id,
        actor_type=ActorType.AGENT,
        sender_id=None,
        body="I can help negotiate on your behalf.",
    )
    session.add(msg)
    await session.flush()

    assert msg.actor_type == ActorType.AGENT
    assert msg.sender_id is None


async def test_bid_creation(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User,
) -> None:
    pickup_time = datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc)
    bid = Bid(
        listing_id=sample_listing.id,
        bidder_id=sample_buyer.id,
        amount=200,
        pickup_latitude=52.20,
        pickup_longitude=5.00,
        pickup_at=pickup_time,
        bid_type=BidType.BUYER,
    )
    session.add(bid)
    await session.flush()

    assert bid.status == BidStatus.PENDING
    assert bid.amount == 200
    assert bid.bid_type == BidType.BUYER


async def test_bid_counter_offer_chain(
    session: AsyncSession, sample_listing: Listing, sample_user: User, sample_buyer: User,
) -> None:
    pickup_time = datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc)

    buyer_bid = Bid(
        listing_id=sample_listing.id,
        bidder_id=sample_buyer.id,
        amount=180,
        pickup_latitude=52.20,
        pickup_longitude=5.00,
        pickup_at=pickup_time,
        bid_type=BidType.BUYER,
    )
    session.add(buyer_bid)
    await session.flush()

    seller_counter = Bid(
        listing_id=sample_listing.id,
        bidder_id=sample_user.id,
        amount=220,
        pickup_latitude=52.37,
        pickup_longitude=4.89,
        pickup_at=pickup_time,
        bid_type=BidType.SELLER,
        parent_bid_id=buyer_bid.id,
        status=BidStatus.COUNTERED,
    )
    session.add(seller_counter)
    await session.flush()

    assert seller_counter.parent_bid_id == buyer_bid.id
    assert seller_counter.bid_type == BidType.SELLER


async def test_message_references_bid(
    session: AsyncSession, sample_listing: Listing, sample_buyer: User,
) -> None:
    pickup_time = datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc)

    bid = Bid(
        listing_id=sample_listing.id,
        bidder_id=sample_buyer.id,
        amount=200,
        pickup_latitude=52.20,
        pickup_longitude=5.00,
        pickup_at=pickup_time,
        bid_type=BidType.BUYER,
    )
    session.add(bid)
    await session.flush()

    convo = Conversation(listing_id=sample_listing.id, buyer_id=sample_buyer.id)
    session.add(convo)
    await session.flush()

    msg = Message(
        conversation_id=convo.id,
        actor_type=ActorType.USER,
        sender_id=sample_buyer.id,
        body="Here's my offer",
        bid_id=bid.id,
    )
    session.add(msg)
    await session.flush()

    assert msg.bid_id == bid.id
