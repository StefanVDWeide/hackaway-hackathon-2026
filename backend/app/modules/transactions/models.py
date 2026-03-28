from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import Base, TimestampMixin
from app.common.types.transactions import TransactionStatus


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    bid_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bids.id"), unique=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int]
    pickup_latitude: Mapped[float]
    pickup_longitude: Mapped[float]
    pickup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[TransactionStatus] = mapped_column(
        default=TransactionStatus.PENDING_ESCROW,
    )
    escrowed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    bid: Mapped["Bid"] = relationship()
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])
