import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models.transaction import Transaction
from app.common.models.user import Wallet
from app.common.types.transactions import TransactionStatus

_TRANSACTION_LOAD_OPTIONS = (
    selectinload(Transaction.bid),
    selectinload(Transaction.buyer),
    selectinload(Transaction.seller),
)


async def get_transaction(
    session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction:
    stmt = (
        select(Transaction)
        .where(Transaction.id == transaction_id)
        .options(*_TRANSACTION_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    txn = result.scalar_one_or_none()
    if not txn:
        raise ValueError("Transaction not found")
    if txn.buyer_id != user_id and txn.seller_id != user_id:
        raise PermissionError("Not a participant in this transaction")
    return txn


async def list_transactions(
    session: AsyncSession, user_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .where(
            (Transaction.buyer_id == user_id) | (Transaction.seller_id == user_id)
        )
        .options(*_TRANSACTION_LOAD_OPTIONS)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def fund_escrow(
    session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction:
    txn = await get_transaction(session, user_id, transaction_id)
    if txn.status != TransactionStatus.PENDING_ESCROW:
        raise ValueError("Transaction is not awaiting escrow")
    if txn.buyer_id != user_id:
        raise PermissionError("Only the buyer can fund escrow")

    wallet = await _get_wallet(session, user_id)
    if wallet.balance < txn.amount:
        raise ValueError("Insufficient balance")

    wallet.balance -= txn.amount
    wallet.held_balance += txn.amount
    txn.status = TransactionStatus.ESCROWED
    txn.escrowed_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(txn)
    return txn


async def release_escrow(
    session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction:
    txn = await get_transaction(session, user_id, transaction_id)
    if txn.status != TransactionStatus.ESCROWED:
        raise ValueError("Transaction is not escrowed")
    if txn.buyer_id != user_id:
        raise PermissionError("Only the buyer can confirm pickup and release escrow")

    buyer_wallet = await _get_wallet(session, txn.buyer_id)
    seller_wallet = await _get_wallet(session, txn.seller_id)

    buyer_wallet.held_balance -= txn.amount
    seller_wallet.balance += txn.amount
    txn.status = TransactionStatus.RELEASED
    txn.released_at = datetime.now(UTC)
    txn.picked_up_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(txn)
    return txn


async def dispute_transaction(
    session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction:
    txn = await get_transaction(session, user_id, transaction_id)
    if txn.status != TransactionStatus.ESCROWED:
        raise ValueError("Can only dispute an escrowed transaction")

    txn.status = TransactionStatus.DISPUTED
    await session.flush()
    await session.refresh(txn)
    return txn


async def refund_transaction(
    session: AsyncSession, transaction_id: uuid.UUID
) -> Transaction:
    """Refund a disputed transaction. This is an admin/system action."""
    stmt = (
        select(Transaction)
        .where(Transaction.id == transaction_id)
        .options(*_TRANSACTION_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    txn = result.scalar_one_or_none()
    if not txn:
        raise ValueError("Transaction not found")
    if txn.status != TransactionStatus.DISPUTED:
        raise ValueError("Can only refund a disputed transaction")

    buyer_wallet = await _get_wallet(session, txn.buyer_id)
    buyer_wallet.held_balance -= txn.amount
    buyer_wallet.balance += txn.amount
    txn.status = TransactionStatus.REFUNDED
    txn.refunded_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(txn)
    return txn


async def get_wallet(session: AsyncSession, user_id: uuid.UUID) -> Wallet:
    return await _get_wallet(session, user_id)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


async def _get_wallet(session: AsyncSession, user_id: uuid.UUID) -> Wallet:
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise ValueError("Wallet not found")
    return wallet
