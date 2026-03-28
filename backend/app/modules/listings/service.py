import uuid
from math import acos, cos, radians, sin

import sqlalchemy as sa
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models.listing import Category, Listing, listing_categories
from app.common.models.user import User
from app.common.types.listings import ListingStatus
from app.integrations.embeddings import generate_embedding
from app.modules.listings.schemas import (
    ListingBrowseParams,
    ListingCreate,
    ListingSearchParams,
    ListingUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LISTING_LOAD_OPTIONS = (
    selectinload(Listing.categories),
    selectinload(Listing.seller),
)


def _haversine_distance(lat: float, lng: float) -> sa.ColumnElement:
    """SQL expression for great-circle distance in km from a point to the seller."""
    earth_radius_km = 6371.0
    lat_r = radians(lat)
    lng_r = radians(lng)
    return (
        earth_radius_km
        * func.acos(
            func.least(
                sa.literal(1.0),
                func.sin(func.radians(User.latitude)) * sin(lat_r)
                + func.cos(func.radians(User.latitude))
                * cos(lat_r)
                * func.cos(func.radians(User.longitude) - lng_r),
            )
        )
    )


def _apply_browse_filters(
    stmt: sa.Select,
    params: ListingBrowseParams | ListingSearchParams,
    *,
    already_joined_user: bool = False,
) -> sa.Select:
    """Apply shared filter predicates to a select statement."""
    if params.category_slug:
        stmt = (
            stmt.join(listing_categories, listing_categories.c.listing_id == Listing.id)
            .join(Category, Category.id == listing_categories.c.category_id)
            .where(Category.slug == params.category_slug)
        )

    if params.condition:
        stmt = stmt.where(Listing.condition == params.condition)

    if params.min_price is not None:
        stmt = stmt.where(Listing.price >= params.min_price)

    if params.max_price is not None:
        stmt = stmt.where(Listing.price <= params.max_price)

    if params.latitude is not None and params.longitude is not None and params.radius_km is not None:
        if not already_joined_user:
            stmt = stmt.join(User, User.id == Listing.seller_id)
        stmt = stmt.where(
            User.latitude.is_not(None),
            User.longitude.is_not(None),
            _haversine_distance(params.latitude, params.longitude) <= params.radius_km,
        )

    return stmt


async def _embed_listing_text(title: str, description: str) -> list[float]:
    """Generate an embedding for a listing's searchable text."""
    text = f"{title}\n{description}"
    return await generate_embedding(text)


def _listing_to_read_dict(listing: Listing) -> dict:
    """Convert a Listing ORM instance to a dict matching ListingRead."""
    return {
        "id": listing.id,
        "seller_id": listing.seller_id,
        "seller_display_name": listing.seller.display_name,
        "title": listing.title,
        "description": listing.description,
        "price": listing.price,
        "condition": listing.condition,
        "status": listing.status,
        "image_url": listing.image_url,
        "categories": listing.categories,
        "created_at": listing.created_at,
        "updated_at": listing.updated_at,
    }


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def create_listing(
    session: AsyncSession, seller_id: uuid.UUID, data: ListingCreate
) -> Listing:
    embedding = await _embed_listing_text(data.title, data.description)

    listing = Listing(
        seller_id=seller_id,
        title=data.title,
        description=data.description,
        price=data.price,
        condition=data.condition,
        status=ListingStatus.DRAFT,
        image_url=data.image_url,
        embedding=embedding,
    )
    session.add(listing)
    await session.flush()

    if data.category_ids:
        for cat_id in data.category_ids:
            await session.execute(
                listing_categories.insert().values(listing_id=listing.id, category_id=cat_id)
            )
        await session.flush()

    await session.refresh(listing, attribute_names=["categories", "seller"])
    return listing


async def update_listing(
    session: AsyncSession, listing_id: uuid.UUID, seller_id: uuid.UUID, data: ListingUpdate
) -> Listing:
    listing = await _get_owned_listing(session, listing_id, seller_id)

    fields = data.model_dump(exclude_unset=True, exclude={"category_ids"})
    for field, value in fields.items():
        setattr(listing, field, value)

    # Regenerate embedding if title or description changed
    if "title" in fields or "description" in fields:
        listing.embedding = await _embed_listing_text(listing.title, listing.description)

    # Update categories if provided
    if data.category_ids is not None:
        await session.execute(
            listing_categories.delete().where(listing_categories.c.listing_id == listing.id)
        )
        for cat_id in data.category_ids:
            await session.execute(
                listing_categories.insert().values(listing_id=listing.id, category_id=cat_id)
            )

    await session.flush()
    await session.refresh(listing, attribute_names=["categories", "seller"])
    return listing


async def delete_listing(
    session: AsyncSession, listing_id: uuid.UUID, seller_id: uuid.UUID
) -> None:
    listing = await _get_owned_listing(session, listing_id, seller_id)
    if listing.status != ListingStatus.DRAFT:
        raise ValueError("Only DRAFT listings can be deleted")
    await session.delete(listing)
    await session.flush()


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


async def publish_listing(
    session: AsyncSession, listing_id: uuid.UUID, seller_id: uuid.UUID
) -> Listing:
    listing = await _get_owned_listing(session, listing_id, seller_id)
    if listing.status != ListingStatus.DRAFT:
        raise ValueError("Only DRAFT listings can be published")
    listing.status = ListingStatus.ACTIVE
    await session.flush()
    await session.refresh(listing, attribute_names=["categories", "seller"])
    return listing


async def archive_listing(
    session: AsyncSession, listing_id: uuid.UUID, seller_id: uuid.UUID
) -> Listing:
    listing = await _get_owned_listing(session, listing_id, seller_id)
    if listing.status != ListingStatus.ACTIVE:
        raise ValueError("Only ACTIVE listings can be archived")
    listing.status = ListingStatus.ARCHIVED
    await session.flush()
    await session.refresh(listing, attribute_names=["categories", "seller"])
    return listing


# ---------------------------------------------------------------------------
# Read / Browse
# ---------------------------------------------------------------------------


async def get_listing(session: AsyncSession, listing_id: uuid.UUID) -> Listing | None:
    stmt = select(Listing).where(Listing.id == listing_id).options(*_LISTING_LOAD_OPTIONS)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_my_listings(
    session: AsyncSession, seller_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> list[Listing]:
    stmt = (
        select(Listing)
        .where(Listing.seller_id == seller_id)
        .options(*_LISTING_LOAD_OPTIONS)
        .order_by(Listing.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def browse_listings(
    session: AsyncSession, params: ListingBrowseParams
) -> list[Listing]:
    stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.ACTIVE)
        .options(*_LISTING_LOAD_OPTIONS)
    )
    stmt = _apply_browse_filters(stmt, params)
    stmt = stmt.order_by(Listing.created_at.desc()).offset(params.offset).limit(params.limit)
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


# ---------------------------------------------------------------------------
# Hybrid search (full-text + semantic, RRF fusion)
# ---------------------------------------------------------------------------


async def search_listings(
    session: AsyncSession, params: ListingSearchParams
) -> list[dict]:
    """
    Hybrid search using Reciprocal Rank Fusion (RRF).

    1. Full-text search via tsvector + ts_rank_cd
    2. Semantic search via pgvector cosine distance
    3. Fuse results with RRF (k=60)
    """
    query_embedding = await generate_embedding(params.query)
    over_fetch = params.limit * 2

    # --- Full-text search ---
    ts_query = func.plainto_tsquery("english", params.query)
    ft_stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.ACTIVE)
        .where(Listing.search_vector.op("@@")(ts_query))
        .options(*_LISTING_LOAD_OPTIONS)
    )
    ft_stmt = _apply_browse_filters(ft_stmt, params)
    ft_stmt = ft_stmt.order_by(
        func.ts_rank_cd(Listing.search_vector, ts_query).desc()
    ).limit(over_fetch)

    # --- Semantic search ---
    sem_stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.ACTIVE)
        .where(Listing.embedding.is_not(None))
        .options(*_LISTING_LOAD_OPTIONS)
    )
    sem_stmt = _apply_browse_filters(sem_stmt, params)
    sem_stmt = sem_stmt.order_by(
        Listing.embedding.cosine_distance(query_embedding)
    ).limit(over_fetch)

    ft_result = await session.execute(ft_stmt)
    sem_result = await session.execute(sem_stmt)

    ft_listings = list(ft_result.scalars().unique().all())
    sem_listings = list(sem_result.scalars().unique().all())

    # --- RRF fusion ---
    fused = _reciprocal_rank_fusion(ft_listings, sem_listings, k=60)
    return [
        {"listing": _listing_to_read_dict(listing), "score": score}
        for listing, score in fused[: params.limit]
    ]


def _reciprocal_rank_fusion(
    *result_lists: list[Listing], k: int = 60
) -> list[tuple[Listing, float]]:
    """Fuse multiple ranked lists using RRF. Returns (listing, score) sorted desc."""
    scores: dict[uuid.UUID, float] = {}
    by_id: dict[uuid.UUID, Listing] = {}

    for result_list in result_lists:
        for rank, listing in enumerate(result_list, start=1):
            scores[listing.id] = scores.get(listing.id, 0.0) + 1.0 / (k + rank)
            by_id[listing.id] = listing

    sorted_ids = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]
    return [(by_id[lid], scores[lid]) for lid in sorted_ids]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_owned_listing(
    session: AsyncSession, listing_id: uuid.UUID, seller_id: uuid.UUID
) -> Listing:
    listing = await get_listing(session, listing_id)
    if not listing:
        raise ValueError("Listing not found")
    if listing.seller_id != seller_id:
        raise PermissionError("You do not own this listing")
    return listing
