import uuid

from pydantic import Field

from app.common.schemas.base import BaseSchema, CreateSchema, ReadSchema
from app.common.types.negotiations import ActorType, BidStatus, BidType


class BidCreate(CreateSchema):
    listing_id: uuid.UUID
    amount: int = Field(gt=0)


class CounterBidCreate(CreateSchema):
    amount: int = Field(gt=0)


class BidRead(ReadSchema):
    listing_id: uuid.UUID
    bidder_id: uuid.UUID
    amount: int
    status: BidStatus
    bid_type: BidType
    parent_bid_id: uuid.UUID | None


class MessageCreate(CreateSchema):
    body: str = Field(min_length=1)


class MessageRead(ReadSchema):
    conversation_id: uuid.UUID
    actor_type: ActorType
    sender_id: uuid.UUID | None
    body: str
    bid_id: uuid.UUID | None
    bid: BidRead | None = None


class ConversationSummary(ReadSchema):
    listing_id: uuid.UUID
    buyer_id: uuid.UUID


class ConversationRead(ReadSchema):
    listing_id: uuid.UUID
    buyer_id: uuid.UUID
    messages: list[MessageRead]
