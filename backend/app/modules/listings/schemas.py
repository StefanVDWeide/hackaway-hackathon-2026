import uuid

from pydantic import Field

from app.common.schemas.base import BaseSchema, CreateSchema, ReadSchema, UpdateSchema
from app.common.types.listings import Condition, ListingStatus


class ListingCreate(CreateSchema):
    title: str = Field(max_length=255)
    description: str
    price: int = Field(gt=0)
    condition: Condition
    image_url: str | None = None
    category_ids: list[uuid.UUID] = Field(default_factory=list)


class ListingUpdate(UpdateSchema):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    price: int | None = Field(default=None, gt=0)
    condition: Condition | None = None
    image_url: str | None = None
    category_ids: list[uuid.UUID] | None = None


class CategoryRead(ReadSchema):
    name: str
    slug: str
    parent_id: uuid.UUID | None


class ListingRead(ReadSchema):
    seller_id: uuid.UUID
    seller_display_name: str
    title: str
    description: str
    price: int
    condition: Condition
    status: ListingStatus
    image_url: str | None
    categories: list[CategoryRead]


class ListingSearchResult(BaseSchema):
    listing: ListingRead
    score: float


class ListingBrowseParams(BaseSchema):
    """Query parameters for browsing listings."""

    category_slug: str | None = None
    condition: Condition | None = None
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = Field(default=None, gt=0)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class ListingSearchParams(BaseSchema):
    """Query parameters for hybrid search."""

    query: str = Field(min_length=1)
    category_slug: str | None = None
    condition: Condition | None = None
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = Field(default=None, gt=0)
    limit: int = Field(default=20, ge=1, le=100)
