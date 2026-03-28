import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db import get_session
from app.modules.negotiations.schemas import (
    BidCreate,
    BidRead,
    ConversationRead,
    ConversationSummary,
    CounterBidCreate,
    MessageCreate,
    MessageRead,
)
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
from app.modules.transactions.schemas import TransactionRead
from app.modules.users.router import get_current_user_id

router = APIRouter(prefix="/negotiations", tags=["negotiations"])


# ---------------------------------------------------------------------------
# Bids
# ---------------------------------------------------------------------------


@router.post("/bids", response_model=BidRead, status_code=status.HTTP_201_CREATED)
async def create_bid(
    data: BidCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        bid = await place_bid(session, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return bid


@router.get("/bids/{bid_id}", response_model=BidRead)
async def get_one_bid(
    bid_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    bid = await get_bid(session, bid_id)
    if not bid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bid not found")
    return bid


@router.get("/me/bids", response_model=list[BidRead])
async def my_bids(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await list_my_bids(session, user_id, offset=offset, limit=limit)


@router.get("/listings/{listing_id}/bids", response_model=list[BidRead])
async def listing_bids(
    listing_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await list_bids_for_listing(session, user_id, listing_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/bids/{bid_id}/counter", response_model=BidRead, status_code=status.HTTP_201_CREATED)
async def counter(
    bid_id: uuid.UUID,
    data: CounterBidCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await counter_bid(session, user_id, bid_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/bids/{bid_id}/accept", response_model=TransactionRead)
async def accept(
    bid_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await accept_bid(session, user_id, bid_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/bids/{bid_id}/reject", response_model=BidRead)
async def reject(
    bid_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await reject_bid(session, user_id, bid_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_convos(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await list_conversations(session, user_id, offset=offset, limit=limit)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_convo(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await get_conversation(session, user_id, conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await send_message(session, user_id, conversation_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
