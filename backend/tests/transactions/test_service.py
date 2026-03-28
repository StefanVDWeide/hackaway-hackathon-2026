"""Tests for transaction service — escrow lifecycle."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models.listing import Listing
from app.common.models.user import User, Wallet
from app.common.types.transactions import TransactionStatus
from app.modules.negotiations.schemas import BidCreate
from app.modules.negotiations.service import accept_bid, place_bid
from app.modules.transactions.service import (
    dispute_transaction,
    fund_escrow,
    get_transaction,
    get_wallet,
    list_transactions,
    refund_transaction,
    release_escrow,
)

pytest_plugins = ["tests.domain_conftest"]


@pytest.fixture
async def buyer_wallet(session: AsyncSession, sample_buyer: User) -> Wallet:
    wallet = Wallet(user_id=sample_buyer.id, balance=1000, held_balance=0)
    session.add(wallet)
    await session.flush()
    await session.refresh(wallet)
    return wallet


@pytest.fixture
async def transaction_setup(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
    sample_wallet: Wallet,
    buyer_wallet: Wallet,
):
    """Place a bid and accept it → creates a PENDING_ESCROW transaction."""
    bid_data = BidCreate(
        listing_id=sample_listing.id,
        amount=200,
    )
    bid = await place_bid(session, sample_buyer.id, bid_data)
    txn = await accept_bid(session, sample_user.id, bid.id)
    return txn


# ---------------------------------------------------------------------------
# fund_escrow
# ---------------------------------------------------------------------------


async def test_fund_escrow(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    buyer_wallet: Wallet,
):
    txn = await fund_escrow(session, sample_buyer.id, transaction_setup.id)
    assert txn.status == TransactionStatus.ESCROWED
    assert txn.escrowed_at is not None

    await session.refresh(buyer_wallet)
    assert buyer_wallet.balance == 800
    assert buyer_wallet.held_balance == 200


async def test_fund_escrow_insufficient_balance(
    session: AsyncSession,
    sample_listing: Listing,
    sample_buyer: User,
    sample_user: User,
    sample_wallet: Wallet,
):
    # Buyer wallet with low balance
    wallet = Wallet(user_id=sample_buyer.id, balance=50, held_balance=0)
    session.add(wallet)
    await session.flush()

    bid_data = BidCreate(
        listing_id=sample_listing.id,
        amount=200,
    )
    bid = await place_bid(session, sample_buyer.id, bid_data)
    txn = await accept_bid(session, sample_user.id, bid.id)

    with pytest.raises(ValueError, match="Insufficient balance"):
        await fund_escrow(session, sample_buyer.id, txn.id)


async def test_fund_escrow_seller_cannot(
    session: AsyncSession,
    transaction_setup,
    sample_user: User,
):
    with pytest.raises(PermissionError, match="buyer"):
        await fund_escrow(session, sample_user.id, transaction_setup.id)


async def test_fund_escrow_wrong_status(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    buyer_wallet: Wallet,
):
    await fund_escrow(session, sample_buyer.id, transaction_setup.id)
    with pytest.raises(ValueError, match="not awaiting escrow"):
        await fund_escrow(session, sample_buyer.id, transaction_setup.id)


# ---------------------------------------------------------------------------
# release_escrow
# ---------------------------------------------------------------------------


async def test_release_escrow(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    sample_user: User,
    buyer_wallet: Wallet,
    sample_wallet: Wallet,
):
    await fund_escrow(session, sample_buyer.id, transaction_setup.id)

    txn = await release_escrow(session, sample_buyer.id, transaction_setup.id)
    assert txn.status == TransactionStatus.RELEASED
    assert txn.released_at is not None
    assert txn.picked_up_at is not None

    await session.refresh(buyer_wallet)
    assert buyer_wallet.held_balance == 0

    await session.refresh(sample_wallet)
    assert sample_wallet.balance == 1200  # original 1000 + 200


async def test_release_escrow_wrong_status(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
):
    with pytest.raises(ValueError, match="not escrowed"):
        await release_escrow(session, sample_buyer.id, transaction_setup.id)


# ---------------------------------------------------------------------------
# dispute
# ---------------------------------------------------------------------------


async def test_dispute_transaction(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    buyer_wallet: Wallet,
):
    await fund_escrow(session, sample_buyer.id, transaction_setup.id)

    txn = await dispute_transaction(session, sample_buyer.id, transaction_setup.id)
    assert txn.status == TransactionStatus.DISPUTED


async def test_dispute_not_escrowed_fails(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
):
    with pytest.raises(ValueError, match="escrowed"):
        await dispute_transaction(session, sample_buyer.id, transaction_setup.id)


# ---------------------------------------------------------------------------
# refund
# ---------------------------------------------------------------------------


async def test_refund_transaction(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    buyer_wallet: Wallet,
):
    await fund_escrow(session, sample_buyer.id, transaction_setup.id)
    await dispute_transaction(session, sample_buyer.id, transaction_setup.id)

    txn = await refund_transaction(session, transaction_setup.id)
    assert txn.status == TransactionStatus.REFUNDED
    assert txn.refunded_at is not None

    await session.refresh(buyer_wallet)
    assert buyer_wallet.balance == 1000  # fully refunded
    assert buyer_wallet.held_balance == 0


async def test_refund_not_disputed_fails(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    buyer_wallet: Wallet,
):
    await fund_escrow(session, sample_buyer.id, transaction_setup.id)
    with pytest.raises(ValueError, match="disputed"):
        await refund_transaction(session, transaction_setup.id)


# ---------------------------------------------------------------------------
# Full lifecycle: bid → escrow → release
# ---------------------------------------------------------------------------


async def test_full_happy_path(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    sample_user: User,
    buyer_wallet: Wallet,
    sample_wallet: Wallet,
):
    """End-to-end: fund escrow → confirm pickup → seller paid."""
    txn = transaction_setup

    # Fund escrow
    txn = await fund_escrow(session, sample_buyer.id, txn.id)
    assert txn.status == TransactionStatus.ESCROWED

    # Release
    txn = await release_escrow(session, sample_buyer.id, txn.id)
    assert txn.status == TransactionStatus.RELEASED

    await session.refresh(buyer_wallet)
    await session.refresh(sample_wallet)
    assert buyer_wallet.balance == 800
    assert buyer_wallet.held_balance == 0
    assert sample_wallet.balance == 1200


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


async def test_get_transaction(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
):
    txn = await get_transaction(session, sample_buyer.id, transaction_setup.id)
    assert txn.id == transaction_setup.id


async def test_get_transaction_not_found(session: AsyncSession, sample_buyer: User):
    with pytest.raises(ValueError, match="not found"):
        await get_transaction(session, sample_buyer.id, uuid.uuid4())


async def test_get_transaction_not_participant(
    session: AsyncSession, transaction_setup
):
    stranger = User(
        email="stranger@example.com", hashed_password="x", display_name="Stranger"
    )
    session.add(stranger)
    await session.flush()

    with pytest.raises(PermissionError, match="participant"):
        await get_transaction(session, stranger.id, transaction_setup.id)


async def test_list_transactions(
    session: AsyncSession,
    transaction_setup,
    sample_buyer: User,
    sample_user: User,
):
    buyer_txns = await list_transactions(session, sample_buyer.id)
    assert len(buyer_txns) == 1

    seller_txns = await list_transactions(session, sample_user.id)
    assert len(seller_txns) == 1


async def test_get_wallet(
    session: AsyncSession, sample_buyer: User, buyer_wallet: Wallet
):
    w = await get_wallet(session, sample_buyer.id)
    assert w.balance == 1000
    assert w.held_balance == 0
