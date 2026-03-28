import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db import get_session
from app.modules.categories.schemas import CategoryCreate, CategoryRead
from app.modules.categories.service import (
    create_category,
    get_all_categories,
    get_category,
)
from app.modules.users.router import get_current_user_id

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: CategoryCreate,
    _user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await create_category(session, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/", response_model=list[CategoryRead])
async def list_all(session: AsyncSession = Depends(get_session)):
    return await get_all_categories(session)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_one(category_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    category = await get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category
