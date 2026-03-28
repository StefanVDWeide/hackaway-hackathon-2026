"""Tests for category schemas."""

import uuid

from app.modules.categories.schemas import CategoryCreate, CategoryRead


def test_category_create_valid():
    data = CategoryCreate(name="Electronics", slug="electronics")
    assert data.name == "Electronics"
    assert data.parent_id is None


def test_category_create_with_parent():
    pid = uuid.uuid4()
    data = CategoryCreate(name="Phones", slug="phones", parent_id=pid)
    assert data.parent_id == pid
