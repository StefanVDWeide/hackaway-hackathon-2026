import uuid
from datetime import datetime

from app.common.schemas.base import ReadSchema
from app.common.types.transactions import TransactionStatus


class TransactionRead(ReadSchema):
    bid_id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    amount: int
    status: TransactionStatus
    escrowed_at: datetime | None
    released_at: datetime | None
    refunded_at: datetime | None
    picked_up_at: datetime | None


class WalletRead(ReadSchema):
    user_id: uuid.UUID
    balance: int
    held_balance: int
