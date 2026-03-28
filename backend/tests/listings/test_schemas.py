"""Tests for listing and category schemas."""

import uuid

import pytest
from pydantic import ValidationError

from app.common.types.listings import Condition
from app.modules.listings.schemas import (
    ListingBrowseParams,
    ListingCreate,
    ListingSearchParams,
    ListingUpdate,
)


def test_listing_create_valid():
    data = ListingCreate(
        title="Item",
        description="Desc",
        price=100,
        condition=Condition.NEW,
    )
    assert data.price == 100
    assert data.category_ids == []


def test_listing_create_price_must_be_positive():
    with pytest.raises(ValidationError):
        ListingCreate(
            title="Item",
            description="Desc",
            price=0,
            condition=Condition.NEW,
        )


def test_listing_create_with_categories():
    cat_id = uuid.uuid4()
    data = ListingCreate(
        title="Item",
        description="Desc",
        price=10,
        condition=Condition.NEW,
        category_ids=[cat_id],
    )
    assert data.category_ids == [cat_id]


def test_listing_update_partial():
    update = ListingUpdate(title="New Title")
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"title": "New Title"}


def test_listing_update_empty():
    update = ListingUpdate()
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {}


def test_browse_params_defaults():
    params = ListingBrowseParams()
    assert params.offset == 0
    assert params.limit == 20
    assert params.category_slug is None


def test_browse_params_negative_price_rejected():
    with pytest.raises(ValidationError):
        ListingBrowseParams(min_price=-1)


def test_search_params_query_required():
    with pytest.raises(ValidationError):
        ListingSearchParams()


def test_search_params_empty_query_rejected():
    with pytest.raises(ValidationError):
        ListingSearchParams(query="")
