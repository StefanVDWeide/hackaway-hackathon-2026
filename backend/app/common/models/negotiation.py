from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import Base, TimestampMixin
from app.common.types.negotiations import ActorType, BidStatus, BidType


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("listing_id", "buyer_id"),)

    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)

    listing: Mapped["Listing"] = relationship(back_populates="conversations")
    buyer: Mapped["User"] = relationship()
    messages: Mapped[list[Message]] = relationship(back_populates="conversation")


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"),
        index=True,
    )
    actor_type: Mapped[ActorType]
    sender_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    bid_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bids.id"))

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    sender: Mapped["User | None"] = relationship()
    bid: Mapped[Bid | None] = relationship()


class Bid(TimestampMixin, Base):
    __tablename__ = "bids"

    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), index=True)
    bidder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int]
    status: Mapped[BidStatus] = mapped_column(default=BidStatus.PENDING)
    bid_type: Mapped[BidType]
    parent_bid_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bids.id"))

    listing: Mapped["Listing"] = relationship(back_populates="bids")
    bidder: Mapped["User"] = relationship(back_populates="bids")
    parent_bid: Mapped[Bid | None] = relationship(remote_side="Bid.id")
