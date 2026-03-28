"""Tests for base schema primitives."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tests.conftest import WidgetCreate, WidgetRead, WidgetUpdate


def test_create_schema_valid() -> None:
    schema = WidgetCreate(name="bolt", color="silver")
    assert schema.name == "bolt"
    assert schema.color == "silver"


def test_create_schema_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        WidgetCreate(name="bolt", color="silver", weight=5)  # type: ignore[call-arg]


def test_update_schema_partial() -> None:
    schema = WidgetUpdate(color="gold")
    dumped = schema.model_dump(exclude_unset=True)
    assert dumped == {"color": "gold"}
    assert "name" not in dumped


def test_update_schema_empty() -> None:
    schema = WidgetUpdate()
    assert schema.model_dump(exclude_unset=True) == {}


def test_read_schema_from_attributes() -> None:
    now = datetime.now(tz=timezone.utc)
    schema = WidgetRead(
        id=uuid.uuid4(),
        name="gear",
        color="brass",
        created_at=now,
        updated_at=now,
    )
    assert isinstance(schema.id, uuid.UUID)
    assert schema.name == "gear"


def test_read_schema_rejects_missing_id() -> None:
    now = datetime.now(tz=timezone.utc)
    with pytest.raises(ValidationError):
        WidgetRead(name="gear", color="brass", created_at=now, updated_at=now)  # type: ignore[call-arg]
