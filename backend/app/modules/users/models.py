from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    is_verified: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    wallet: Mapped[Wallet] = relationship(back_populates="user", uselist=False)
    listings: Mapped[list["Listing"]] = relationship(back_populates="seller")
    bids: Mapped[list["Bid"]] = relationship(back_populates="bidder")


class Wallet(TimestampMixin, Base):
    __tablename__ = "wallets"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    balance: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    held_balance: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    user: Mapped[User] = relationship(back_populates="wallet")
