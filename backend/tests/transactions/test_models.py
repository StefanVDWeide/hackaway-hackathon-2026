"""Tests for Transaction model and escrow flow."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.types.negotiations import BidStatus, BidType
from app.common.types.transactions import TransactionStatus
from app.common.models.negotiation import Bid
from app.common.models.transaction import Transaction
from app.common.models.user import User, Wallet
from app.common.models.listing import Listing

pytest_plugins = ["tests.domain_conftest"]


async def _create_accepted_bid(
    session: AsyncSession, listing: Listing, buyer: User,
) -> Bid:
    pickup_time = datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc)
    bid = Bid(
        listing_id=listing.id,
        bidder_id=buyer.id,
        amount=200,
        pickup_latitude=52.20,
        pickup_longitude=5.00,
        pickup_at=pickup_time,
        bid_type=BidType.BUYER,
        status=BidStatus.ACCEPTED,
    )
    session.add(bid)
    await session.flush()
    return bid


async def test_transaction_creation(
    session: AsyncSession,
    sample_listing: Listing,
    sample_user: User,
    sample_buyer: User,
) -> None:
    bid = await _create_accepted_bid(session, sample_listing, sample_buyer)

    txn = Transaction(
        bid_id=bid.id,
        buyer_id=sample_buyer.id,
        seller_id=sample_user.id,
        amount=bid.amount,
        pickup_latitude=bid.pickup_latitude,
        pickup_longitude=bid.pickup_longitude,
        pickup_at=bid.pickup_at,
    )
    session.add(txn)
    await session.flush()

    assert txn.status == TransactionStatus.PENDING_ESCROW
    assert txn.amount == 200


async def test_escrow_flow(
    session: AsyncSession,
    sample_listing: Listing,
    sample_user: User,
    sample_buyer: User,
    sample_wallet: Wallet,
) -> None:
    buyer_wallet = Wallet(user_id=sample_buyer.id, balance=500, held_balance=0)
    session.add(buyer_wallet)
    await session.flush()

    bid = await _create_accepted_bid(session, sample_listing, sample_buyer)

    txn = Transaction(
        bid_id=bid.id,
        buyer_id=sample_buyer.id,
        seller_id=sample_user.id,
        amount=bid.amount,
        pickup_latitude=bid.pickup_latitude,
        pickup_longitude=bid.pickup_longitude,
        pickup_at=bid.pickup_at,
    )
    session.add(txn)
    await session.flush()

    # Escrow: lock funds
    now = datetime.now(tz=timezone.utc)
    buyer_wallet.balance -= txn.amount
    buyer_wallet.held_balance += txn.amount
    txn.status = TransactionStatus.ESCROWED
    txn.escrowed_at = now
    await session.flush()

    assert buyer_wallet.balance == 300
    assert buyer_wallet.held_balance == 200
    assert txn.status == TransactionStatus.ESCROWED

    # Release: buyer confirms pickup
    txn.picked_up_at = now
    buyer_wallet.held_balance -= txn.amount
    sample_wallet.balance += txn.amount
    txn.status = TransactionStatus.RELEASED
    txn.released_at = now
    await session.flush()

    assert buyer_wallet.held_balance == 0
    assert sample_wallet.balance == 1200  # 1000 + 200
    assert txn.status == TransactionStatus.RELEASED


async def test_refund_flow(
    session: AsyncSession,
    sample_listing: Listing,
    sample_user: User,
    sample_buyer: User,
) -> None:
    buyer_wallet = Wallet(user_id=sample_buyer.id, balance=500, held_balance=0)
    session.add(buyer_wallet)
    await session.flush()

    bid = await _create_accepted_bid(session, sample_listing, sample_buyer)

    txn = Transaction(
        bid_id=bid.id,
        buyer_id=sample_buyer.id,
        seller_id=sample_user.id,
        amount=bid.amount,
        pickup_latitude=bid.pickup_latitude,
        pickup_longitude=bid.pickup_longitude,
        pickup_at=bid.pickup_at,
    )
    session.add(txn)
    await session.flush()

    # Escrow
    now = datetime.now(tz=timezone.utc)
    buyer_wallet.balance -= txn.amount
    buyer_wallet.held_balance += txn.amount
    txn.status = TransactionStatus.ESCROWED
    txn.escrowed_at = now
    await session.flush()

    # Refund
    buyer_wallet.held_balance -= txn.amount
    buyer_wallet.balance += txn.amount
    txn.status = TransactionStatus.REFUNDED
    txn.refunded_at = now
    await session.flush()

    assert buyer_wallet.balance == 500  # back to original
    assert buyer_wallet.held_balance == 0
    assert txn.status == TransactionStatus.REFUNDED


async def test_one_transaction_per_bid(
    session: AsyncSession,
    sample_listing: Listing,
    sample_user: User,
    sample_buyer: User,
) -> None:
    import pytest
    from sqlalchemy.exc import IntegrityError

    bid = await _create_accepted_bid(session, sample_listing, sample_buyer)

    txn1 = Transaction(
        bid_id=bid.id,
        buyer_id=sample_buyer.id,
        seller_id=sample_user.id,
        amount=200,
        pickup_latitude=52.20,
        pickup_longitude=5.00,
        pickup_at=bid.pickup_at,
    )
    session.add(txn1)
    await session.flush()

    txn2 = Transaction(
        bid_id=bid.id,
        buyer_id=sample_buyer.id,
        seller_id=sample_user.id,
        amount=200,
        pickup_latitude=52.20,
        pickup_longitude=5.00,
        pickup_at=bid.pickup_at,
    )
    session.add(txn2)
    with pytest.raises(IntegrityError):
        await session.flush()
