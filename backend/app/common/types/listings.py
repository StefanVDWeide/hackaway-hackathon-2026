from enum import StrEnum


class Condition(StrEnum):
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class ListingStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SOLD = "sold"
    ARCHIVED = "archived"
