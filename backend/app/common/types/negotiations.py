from enum import StrEnum


class ActorType(StrEnum):
    USER = "user"
    AGENT = "agent"


class BidStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    EXPIRED = "expired"


class BidType(StrEnum):
    BUYER = "buyer"
    SELLER = "seller"
