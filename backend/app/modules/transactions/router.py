import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db import get_session
from app.modules.transactions.schemas import TransactionRead, WalletRead
from app.modules.transactions.service import (
    dispute_transaction,
    fund_escrow,
    get_transaction,
    get_wallet,
    list_transactions,
    release_escrow,
    refund_transaction,
)
from app.modules.users.router import get_current_user_id

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=list[TransactionRead])
async def list_txns(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await list_transactions(session, user_id, offset=offset, limit=limit)


@router.get("/wallet", response_model=WalletRead)
async def wallet(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await get_wallet(session, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_one(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await get_transaction(session, user_id, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{transaction_id}/escrow", response_model=TransactionRead)
async def escrow(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await fund_escrow(session, user_id, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{transaction_id}/release", response_model=TransactionRead)
async def release(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await release_escrow(session, user_id, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{transaction_id}/dispute", response_model=TransactionRead)
async def dispute(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await dispute_transaction(session, user_id, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{transaction_id}/refund", response_model=TransactionRead)
async def refund(
    transaction_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Refund a disputed transaction. Currently unauthenticated (admin action)."""
    try:
        return await refund_transaction(session, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
