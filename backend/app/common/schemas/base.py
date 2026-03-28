import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with shared Pydantic config."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class CreateSchema(BaseSchema):
    """Base schema for creation payloads. Subclass and add fields."""


class UpdateSchema(BaseSchema):
    """Base schema for update payloads. All fields should be Optional."""


class ReadSchema(BaseSchema):
    """Base schema for read responses — includes id and timestamps."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
