"""Управление пользователями."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Role
from app.schemas import UserOut, UserCreate, UserUpdate, RoleOut
from app.security import get_current_user, hash_password, require_role

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Список всех пользователей. Доступно всем авторизованным."""
    stmt = select(User).options(selectinload(User.role)).order_by(User.full_name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/",
    response_model=UserOut,
    dependencies=[Depends(require_role("admin"))],
)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создание нового пользователя. Только администратор."""
    # Проверка уникальности логина
    existing = await db.execute(select(User).where(User.login == payload.login))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует",
        )

    user = User(
        login=payload.login,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        email=payload.email,
        role_id=payload.role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user, ["role"])
    return user


@router.patch(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_role("admin"))],
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Изменение пользователя. Только администратор."""
    stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Пользователь не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user, ["role"])
    return user


@router.get("/roles/", response_model=List[RoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Список доступных ролей."""
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all()
