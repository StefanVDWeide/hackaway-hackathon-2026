import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models.listing import Listing
from app.common.models.negotiation import Bid, Conversation, Message
from app.common.models.transaction import Transaction
from app.common.models.user import User
from app.common.types.listings import ListingStatus
from app.common.types.negotiations import ActorType, BidStatus, BidType
from app.common.types.transactions import TransactionStatus
from app.modules.negotiations.schemas import BidCreate, CounterBidCreate, MessageCreate

_BID_LOAD_OPTIONS = (
    selectinload(Bid.listing),
    selectinload(Bid.bidder),
)

_CONVERSATION_LOAD_OPTIONS = (
    selectinload(Conversation.messages).selectinload(Message.bid),
    selectinload(Conversation.listing),
    selectinload(Conversation.buyer),
)


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


async def get_or_create_conversation(
    session: AsyncSession, listing_id: uuid.UUID, buyer_id: uuid.UUID
) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.listing_id == listing_id,
        Conversation.buyer_id == buyer_id,
    )
    result = await session.execute(stmt)
    conv = result.scalar_one_or_none()
    if conv:
        return conv

    conv = Conversation(listing_id=listing_id, buyer_id=buyer_id)
    session.add(conv)
    await session.flush()
    await session.refresh(conv)
    return conv


async def list_conversations(
    session: AsyncSession, user_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .join(Listing, Listing.id == Conversation.listing_id)
        .where(
            (Conversation.buyer_id == user_id) | (Listing.seller_id == user_id)
        )
        .order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_conversation(
    session: AsyncSession, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation:
    stmt = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(*_CONVERSATION_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise ValueError("Conversation not found")

    # Check access: user must be buyer or listing seller
    if conv.buyer_id != user_id and conv.listing.seller_id != user_id:
        raise PermissionError("Not a participant in this conversation")
    return conv


async def send_message(
    session: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    data: MessageCreate,
) -> Message:
    conv = await get_conversation(session, user_id, conversation_id)

    msg = Message(
        conversation_id=conv.id,
        actor_type=ActorType.USER,
        sender_id=user_id,
        body=data.body,
    )
    session.add(msg)
    await session.flush()
    await session.refresh(msg)
    return msg


# ---------------------------------------------------------------------------
# Bids
# ---------------------------------------------------------------------------


async def place_bid(
    session: AsyncSession, buyer_id: uuid.UUID, data: BidCreate
) -> Bid:
    listing = await session.get(Listing, data.listing_id)
    if not listing:
        raise ValueError("Listing not found")
    if listing.status != ListingStatus.ACTIVE:
        raise ValueError("Listing is not active")
    if listing.seller_id == buyer_id:
        raise ValueError("Cannot bid on your own listing")

    # One pending bid per buyer per listing
    existing = await session.execute(
        select(Bid).where(
            Bid.listing_id == data.listing_id,
            Bid.bidder_id == buyer_id,
            Bid.status == BidStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("You already have a pending bid on this listing")

    bid = Bid(
        listing_id=data.listing_id,
        bidder_id=buyer_id,
        amount=data.amount,
        pickup_latitude=data.pickup_latitude,
        pickup_longitude=data.pickup_longitude,
        pickup_at=data.pickup_at,
        bid_type=BidType.BUYER,
        status=BidStatus.PENDING,
    )
    session.add(bid)
    await session.flush()

    # Get or create conversation and add a message
    conv = await get_or_create_conversation(session, data.listing_id, buyer_id)
    msg = Message(
        conversation_id=conv.id,
        actor_type=ActorType.USER,
        sender_id=buyer_id,
        body=f"Bid placed: {data.amount}",
        bid_id=bid.id,
    )
    session.add(msg)
    await session.flush()
    await session.refresh(bid)
    return bid


async def counter_bid(
    session: AsyncSession, user_id: uuid.UUID, bid_id: uuid.UUID, data: CounterBidCreate
) -> Bid:
    original = await _load_bid(session, bid_id)
    if original.status != BidStatus.PENDING:
        raise ValueError("Can only counter a pending bid")

    listing = await session.get(Listing, original.listing_id)
    is_seller = listing.seller_id == user_id

    # Determine if user is the buyer in this negotiation (find original bid in chain)
    root = original
    while root.parent_bid_id:
        root = await _load_bid(session, root.parent_bid_id)
    is_buyer = root.bidder_id == user_id

    if not is_seller and not is_buyer:
        raise PermissionError("Not a participant in this negotiation")

    # Seller counters BUYER bids, buyer counters SELLER bids
    if is_seller and original.bid_type != BidType.BUYER:
        raise ValueError("Seller can only counter buyer bids")
    if is_buyer and original.bid_type != BidType.SELLER:
        raise ValueError("Buyer can only counter seller bids")

    original.status = BidStatus.COUNTERED

    new_bid_type = BidType.SELLER if is_seller else BidType.BUYER
    counter = Bid(
        listing_id=original.listing_id,
        bidder_id=user_id,
        amount=data.amount,
        pickup_latitude=data.pickup_latitude,
        pickup_longitude=data.pickup_longitude,
        pickup_at=data.pickup_at,
        bid_type=new_bid_type,
        status=BidStatus.PENDING,
        parent_bid_id=original.id,
    )
    session.add(counter)
    await session.flush()

    # Determine the buyer for the conversation
    conv_buyer_id = original.bidder_id if is_seller else user_id
    conv = await get_or_create_conversation(session, original.listing_id, conv_buyer_id)
    msg = Message(
        conversation_id=conv.id,
        actor_type=ActorType.USER,
        sender_id=user_id,
        body=f"Counter-offer: {data.amount}",
        bid_id=counter.id,
    )
    session.add(msg)
    await session.flush()
    await session.refresh(counter)
    return counter


async def accept_bid(
    session: AsyncSession, user_id: uuid.UUID, bid_id: uuid.UUID
) -> Transaction:
    bid = await _load_bid(session, bid_id)
    if bid.status != BidStatus.PENDING:
        raise ValueError("Can only accept a pending bid")

    listing = await session.get(Listing, bid.listing_id)
    _check_opposite_party(user_id, bid, listing)

    bid.status = BidStatus.ACCEPTED

    # Auto-reject all other pending bids on this listing
    other_bids = await session.execute(
        select(Bid).where(
            Bid.listing_id == bid.listing_id,
            Bid.status == BidStatus.PENDING,
            Bid.id != bid.id,
        )
    )
    for other in other_bids.scalars().all():
        other.status = BidStatus.REJECTED

    # Mark listing as sold
    listing.status = ListingStatus.SOLD

    # Determine the buyer — always the original conversation buyer
    # Find the conversation for this bid chain
    root_bid = bid
    while root_bid.parent_bid_id:
        root_bid = await _load_bid(session, root_bid.parent_bid_id)
    buyer_id = root_bid.bidder_id  # The person who placed the first bid

    txn = Transaction(
        bid_id=bid.id,
        buyer_id=buyer_id,
        seller_id=listing.seller_id,
        amount=bid.amount,
        pickup_latitude=bid.pickup_latitude,
        pickup_longitude=bid.pickup_longitude,
        pickup_at=bid.pickup_at,
        status=TransactionStatus.PENDING_ESCROW,
    )
    session.add(txn)
    await session.flush()

    # Message in conversation
    conv = await get_or_create_conversation(session, bid.listing_id, buyer_id)
    msg = Message(
        conversation_id=conv.id,
        actor_type=ActorType.USER,
        sender_id=user_id,
        body="Bid accepted",
        bid_id=bid.id,
    )
    session.add(msg)
    await session.flush()
    await session.refresh(txn)
    return txn


async def reject_bid(
    session: AsyncSession, user_id: uuid.UUID, bid_id: uuid.UUID
) -> Bid:
    bid = await _load_bid(session, bid_id)
    if bid.status != BidStatus.PENDING:
        raise ValueError("Can only reject a pending bid")

    listing = await session.get(Listing, bid.listing_id)
    _check_opposite_party(user_id, bid, listing)

    bid.status = BidStatus.REJECTED
    await session.flush()

    # Find buyer for conversation
    root_bid = bid
    while root_bid.parent_bid_id:
        root_bid = await _load_bid(session, root_bid.parent_bid_id)
    conv = await get_or_create_conversation(session, bid.listing_id, root_bid.bidder_id)
    msg = Message(
        conversation_id=conv.id,
        actor_type=ActorType.USER,
        sender_id=user_id,
        body="Bid rejected",
        bid_id=bid.id,
    )
    session.add(msg)
    await session.flush()
    await session.refresh(bid)
    return bid


async def get_bid(session: AsyncSession, bid_id: uuid.UUID) -> Bid | None:
    stmt = select(Bid).where(Bid.id == bid_id).options(*_BID_LOAD_OPTIONS)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_bids_for_listing(
    session: AsyncSession, user_id: uuid.UUID, listing_id: uuid.UUID
) -> list[Bid]:
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError("Listing not found")
    if listing.seller_id != user_id:
        raise PermissionError("You do not own this listing")

    stmt = (
        select(Bid)
        .where(Bid.listing_id == listing_id)
        .order_by(Bid.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_my_bids(
    session: AsyncSession, user_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> list[Bid]:
    stmt = (
        select(Bid)
        .where(Bid.bidder_id == user_id)
        .order_by(Bid.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _load_bid(session: AsyncSession, bid_id: uuid.UUID) -> Bid:
    bid = await session.get(Bid, bid_id)
    if not bid:
        raise ValueError("Bid not found")
    return bid


def _check_opposite_party(user_id: uuid.UUID, bid: Bid, listing: Listing) -> None:
    """Only the opposite party can accept/reject a bid."""
    is_seller = listing.seller_id == user_id
    is_original_buyer = bid.bidder_id != user_id and is_seller

    if bid.bid_type == BidType.BUYER and not is_seller:
        raise PermissionError("Only the seller can accept/reject buyer bids")
    if bid.bid_type == BidType.SELLER and is_seller:
        raise PermissionError("Only the buyer can accept/reject seller bids")
    if not is_seller and bid.bidder_id == user_id:
        raise PermissionError("Cannot accept/reject your own bid")
