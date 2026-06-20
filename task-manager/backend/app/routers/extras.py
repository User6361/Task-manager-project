"""Уведомления и теги."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Notification, Tag, User
from app.schemas import NotificationOut, TagOut, TagCreate
from app.security import get_current_user, require_role


# ---------------- Уведомления ----------------
notif_router = APIRouter(prefix="/notifications", tags=["Уведомления"])


@notif_router.get("/", response_model=List[NotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
    only_unread: bool = False,
):
    """Уведомления текущего пользователя."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == current.id)
        .order_by(Notification.created_at.desc())
    )
    if only_unread:
        stmt = stmt.where(Notification.is_read.is_(False))
    result = await db.execute(stmt)
    return result.scalars().all()


@notif_router.post("/{notif_id}/read")
async def mark_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Отметить уведомление прочитанным."""
    notif = await db.get(Notification, notif_id)
    if not notif or notif.user_id != current.id:
        raise HTTPException(404, "Уведомление не найдено")
    notif.is_read = True
    await db.commit()
    return {"ok": True}


# ---------------- Теги ----------------
tags_router = APIRouter(prefix="/tags", tags=["Теги"])


@tags_router.get("/", response_model=List[TagOut])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Список всех тегов."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()


@tags_router.post(
    "/",
    response_model=TagOut,
    dependencies=[Depends(require_role("manager", "admin"))],
)
async def create_tag(payload: TagCreate, db: AsyncSession = Depends(get_db)):
    """Создание тега."""
    tag = Tag(name=payload.name, color=payload.color)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag
