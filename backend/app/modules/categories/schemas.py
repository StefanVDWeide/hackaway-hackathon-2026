import uuid

from pydantic import Field

from app.common.schemas.base import CreateSchema, ReadSchema


class CategoryCreate(CreateSchema):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=100)
    parent_id: uuid.UUID | None = None


class CategoryRead(ReadSchema):
    name: str
    slug: str
    parent_id: uuid.UUID | None
