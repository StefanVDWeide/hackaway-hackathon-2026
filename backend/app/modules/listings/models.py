from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Computed, ForeignKey, Index, String, Table, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import Base, TimestampMixin
from app.common.types.listings import Condition, ListingStatus


listing_categories = Table(
    "listing_categories",
    Base.metadata,
    Column("listing_id", ForeignKey("listings.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)


class Listing(TimestampMixin, Base):
    __tablename__ = "listings"

    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int]
    condition: Mapped[Condition]
    status: Mapped[ListingStatus] = mapped_column(default=ListingStatus.DRAFT)
    image_url: Mapped[str | None] = mapped_column(String(500))

    # --- Search ---
    # Full-text search: auto-generated tsvector from title (weight A) + description (weight B)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(description, '')), 'B')",
            persisted=True,
        ),
    )
    # Semantic search: embedding vector (1536 dims — OpenAI ada-002 / similar)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    __table_args__ = (
        Index("ix_listings_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_listings_embedding", "embedding", postgresql_using="hnsw",
              postgresql_ops={"embedding": "vector_cosine_ops"}),
        Index("ix_listings_seller_id", "seller_id"),
    )

    seller: Mapped["User"] = relationship(back_populates="listings")
    categories: Mapped[list[Category]] = relationship(
        secondary=listing_categories, back_populates="listings",
    )
    bids: Mapped[list["Bid"]] = relationship(back_populates="listing")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="listing")


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id"))

    parent: Mapped[Category | None] = relationship(remote_side="Category.id")
    listings: Mapped[list[Listing]] = relationship(
        secondary=listing_categories, back_populates="categories",
    )
