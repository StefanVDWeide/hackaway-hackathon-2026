import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db import get_session
from app.common.types.listings import Condition
from app.modules.listings.schemas import (
    ListingBrowseParams,
    ListingCreate,
    ListingRead,
    ListingSearchParams,
    ListingSearchResult,
    ListingUpdate,
)
from app.modules.listings.service import (
    archive_listing,
    browse_listings,
    create_listing,
    delete_listing,
    get_listing,
    get_my_listings,
    publish_listing,
    search_listings,
    update_listing,
)
from app.modules.users.router import get_current_user_id

router = APIRouter(prefix="/listings", tags=["listings"])


# ---------------------------------------------------------------------------
# Buyer-side (public)
# ---------------------------------------------------------------------------


@router.get("/search", response_model=list[ListingSearchResult])
async def search(
    query: str = Query(min_length=1),
    category_slug: str | None = None,
    condition: Condition | None = None,
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = Query(default=None, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    params = ListingSearchParams(
        query=query,
        category_slug=category_slug,
        condition=condition,
        min_price=min_price,
        max_price=max_price,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit,
    )
    return await search_listings(session, params)


@router.get("/me", response_model=list[ListingRead])
async def my_listings(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    listings = await get_my_listings(session, user_id, offset=offset, limit=limit)
    return listings


@router.get("/{listing_id}", response_model=ListingRead)
async def get_one(listing_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    listing = await get_listing(session, listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


@router.get("/", response_model=list[ListingRead])
async def browse(
    category_slug: str | None = None,
    condition: Condition | None = None,
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = Query(default=None, gt=0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    params = ListingBrowseParams(
        category_slug=category_slug,
        condition=condition,
        min_price=min_price,
        max_price=max_price,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        offset=offset,
        limit=limit,
    )
    return await browse_listings(session, params)


# ---------------------------------------------------------------------------
# Seller-side (authenticated)
# ---------------------------------------------------------------------------


@router.post("/", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: ListingCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await create_listing(session, user_id, data)


@router.patch("/{listing_id}", response_model=ListingRead)
async def update(
    listing_id: uuid.UUID,
    data: ListingUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await update_listing(session, listing_id, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{listing_id}/publish", response_model=ListingRead)
async def publish(
    listing_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await publish_listing(session, listing_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{listing_id}/archive", response_model=ListingRead)
async def archive(
    listing_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await archive_listing(session, listing_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    listing_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        await delete_listing(session, listing_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
