from enum import StrEnum


class TransactionStatus(StrEnum):
    PENDING_ESCROW = "pending_escrow"
    ESCROWED = "escrowed"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
