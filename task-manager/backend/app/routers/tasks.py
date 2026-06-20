"""Управление задачами — основной роутер системы."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Task, TaskStatus, User, Tag, Comment, TaskHistory, Notification,
    NotificationType,
)
from app.schemas import (
    TaskOut, TaskCreate, TaskUpdate, TaskHistoryOut,
    CommentCreate, CommentOut,
    AutoAssignResponse, ReportItem, ReportResponse,
)
from app.security import get_current_user, require_role
from app.services import (
    auto_assign_task, calc_task_priority, calc_urgency_from_deadline,
)

router = APIRouter(prefix="/tasks", tags=["Задачи"])


# ---------------------------------------------------------------
#                       Утилиты сериализации
# ---------------------------------------------------------------
def _serialize_task(task: Task) -> dict:
    """Подготовка задачи к ответу с разворачиванием имён связанных сущностей."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "importance": task.importance,
        "priority": task.priority,
        "deadline": task.deadline,
        "project_id": task.project_id,
        "assignee_id": task.assignee_id,
        "assignee_name": task.assignee.full_name if task.assignee else None,
        "author_id": task.author_id,
        "author_name": task.author.full_name if task.author else None,
        "parent_task_id": task.parent_task_id,
        "is_escalated": task.is_escalated,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "tags": task.tags,
    }


async def _load_task(db: AsyncSession, task_id: int) -> Task:
    """Загрузка задачи со всеми связанными сущностями."""
    stmt = (
        select(Task)
        .where(Task.id == task_id)
        .options(
            selectinload(Task.assignee),
            selectinload(Task.author),
            selectinload(Task.tags),
        )
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Задача не найдена")
    return task


# ---------------------------------------------------------------
#                       CRUD
# ---------------------------------------------------------------
@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
    project_id: Optional[int] = None,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    assignee_id: Optional[int] = None,
    only_mine: bool = False,
):
    """Список задач с фильтрами."""
    stmt = (
        select(Task)
        .options(
            selectinload(Task.assignee),
            selectinload(Task.author),
            selectinload(Task.tags),
        )
        .order_by(Task.priority.desc(), Task.deadline.asc().nullslast())
    )

    conditions = []
    if project_id:
        conditions.append(Task.project_id == project_id)
    if status_filter:
        conditions.append(Task.status == status_filter)
    if assignee_id:
        conditions.append(Task.assignee_id == assignee_id)
    if only_mine or current.role.code == "executor":
        # Исполнитель видит только свои задачи
        conditions.append(Task.assignee_id == current.id)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return [_serialize_task(t) for t in tasks]


@router.post(
    "/",
    response_model=TaskOut,
    dependencies=[Depends(require_role("manager", "admin"))],
)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Создание задачи. Если assignee_id не указан — выполняется
    автоматическое распределение по алгоритму из подраздела 2.4.
    Приоритет рассчитывается автоматически по формуле 2.3.
    """
    task = Task(
        title=payload.title,
        description=payload.description,
        importance=payload.importance,
        deadline=payload.deadline,
        project_id=payload.project_id,
        author_id=current.id,
        assignee_id=payload.assignee_id,
        parent_task_id=payload.parent_task_id,
    )

 
    # Расчёт приоритета (формула 2.3)
    urgency = calc_urgency_from_deadline(payload.deadline)
    from app.services import calc_priority
    task.priority = calc_priority(payload.importance, urgency)

    # Автораспределение, если исполнитель не задан
    if task.assignee_id is None:
        chosen, _ = await auto_assign_task(db, task)
        if chosen:
            task.assignee_id = chosen.id

    # Привязка тегов
    if payload.tag_ids:
        tag_result = await db.execute(
            select(Tag).where(Tag.id.in_(payload.tag_ids))
        )
        task.tags = list(tag_result.scalars().all())

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Уведомление исполнителю
    if task.assignee_id and task.assignee_id != current.id:
        notif = Notification(
            user_id=task.assignee_id,
            task_id=task.id,
            type=NotificationType.TASK_ASSIGNED,
            message=f"Вам назначена задача: «{task.title}»",
        )
        db.add(notif)
        await db.commit()

    task = await _load_task(db, task.id)
    return _serialize_task(task)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Получение задачи по ID."""
    task = await _load_task(db, task_id)
    return _serialize_task(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Изменение задачи. Исполнитель может менять только статус."""
    task = await _load_task(db, task_id)

    # Исполнитель ограничен в правах
    if current.role.code == "executor":
        if task.assignee_id != current.id:
            raise HTTPException(403, "Можно изменять только свои задачи")
        # Допускаем для исполнителя только смену статуса
        allowed = {"status"}
        provided = set(payload.model_dump(exclude_unset=True).keys())
        if not provided.issubset(allowed):
            raise HTTPException(
                403, "Исполнителю разрешено менять только статус задачи"
            )

    # История изменений
    changes = payload.model_dump(exclude_unset=True)
    for field, new_val in changes.items():
        if field == "tag_ids":
            continue

            # Нормализуем deadline
        if field == "deadline" and isinstance(new_val, datetime) and new_val.tzinfo is not None:
            new_val = new_val.astimezone(timezone.utc).replace(tzinfo=None)
    

        old_val = getattr(task, field)
        if old_val != new_val:
            history = TaskHistory(
                task_id=task.id,
                user_id=current.id,
                field=field,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None,
            )
            db.add(history)
            setattr(task, field, new_val)

    # Если поменялась важность или дедлайн — пересчитать приоритет
    if "importance" in changes or "deadline" in changes:
        task.priority = calc_task_priority(task)

    # Теги
    if payload.tag_ids is not None:
        tag_result = await db.execute(
            select(Tag).where(Tag.id.in_(payload.tag_ids))
        )
        task.tags = list(tag_result.scalars().all())

    await db.commit()
    task = await _load_task(db, task.id)
    return _serialize_task(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("manager", "admin"))],
)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление задачи. Доступно руководителю и администратору."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Задача не найдена")
    await db.delete(task)
    await db.commit()


# ---------------------------------------------------------------
#                       Канбан-доска
# ---------------------------------------------------------------
@router.get("/board/view", response_model=Dict[str, List[TaskOut]])
async def get_board(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
    project_id: Optional[int] = None,
):
    """Канбан-доска: задачи, сгруппированные по статусам."""
    stmt = (
        select(Task)
        .options(
            selectinload(Task.assignee),
            selectinload(Task.author),
            selectinload(Task.tags),
        )
        .order_by(Task.priority.desc(), Task.deadline.asc().nullslast())
    )
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    if current.role.code == "executor":
        stmt = stmt.where(Task.assignee_id == current.id)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    board: Dict[str, List[Any]] = {s.value: [] for s in TaskStatus}
    for t in tasks:
        board[t.status.value].append(_serialize_task(t))
    return board


# ---------------------------------------------------------------
#                       Автораспределение
# ---------------------------------------------------------------
@router.post(
    "/auto-assign/{task_id}",
    response_model=AutoAssignResponse,
    dependencies=[Depends(require_role("manager", "admin"))],
)
async def trigger_auto_assign(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Принудительный запуск автораспределения для существующей задачи.
    Возвращает подробности расчёта (для демонстрации работы алгоритма).
    """
    task = await _load_task(db, task_id)
    chosen, candidates = await auto_assign_task(db, task)
    if not chosen:
        raise HTTPException(
            400, "Не найдено активных исполнителей для автораспределения"
        )
    await db.commit()

    return AutoAssignResponse(
        task_id=task.id,
        assignee_id=chosen.id,
        assignee_name=chosen.full_name,
        weight=next(
            (c["weight"] for c in candidates if c["is_chosen"]), 0.0
        ),
        candidates=candidates,
    )


# ---------------------------------------------------------------
#                       Комментарии
# ---------------------------------------------------------------
@router.get("/{task_id}/comments", response_model=List[CommentOut])
async def list_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Комментарии к задаче."""
    stmt = (
        select(Comment)
        .where(Comment.task_id == task_id)
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at)
    )
    result = await db.execute(stmt)
    comments = result.scalars().all()
    return [
        {
            "id": c.id, "task_id": c.task_id, "author_id": c.author_id,
            "author_name": c.author.full_name if c.author else None,
            "text": c.text, "created_at": c.created_at,
        }
        for c in comments
    ]


@router.post("/{task_id}/comments", response_model=CommentOut)
async def add_comment(
    task_id: int,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Добавление комментария к задаче."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Задача не найдена")

    comment = Comment(task_id=task_id, author_id=current.id, text=payload.text)
    db.add(comment)
    await db.commit()
    await db.refresh(comment, ["author"])

    # Уведомление исполнителю / автору, если не сам себе пишет
    notify_user_id = None
    if task.assignee_id and task.assignee_id != current.id:
        notify_user_id = task.assignee_id
    elif task.author_id != current.id:
        notify_user_id = task.author_id

    if notify_user_id:
        notif = Notification(
            user_id=notify_user_id,
            task_id=task_id,
            type=NotificationType.TASK_COMMENTED,
            message=f"Новый комментарий по задаче «{task.title}»",
        )
        db.add(notif)
        await db.commit()

    return {
        "id": comment.id, "task_id": comment.task_id,
        "author_id": comment.author_id, "author_name": comment.author.full_name,
        "text": comment.text, "created_at": comment.created_at,
    }


# ---------------------------------------------------------------
#                       История изменений
# ---------------------------------------------------------------
@router.get("/{task_id}/history", response_model=List[TaskHistoryOut])
async def get_task_history(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """История изменений задачи."""
    stmt = (
        select(TaskHistory)
        .where(TaskHistory.task_id == task_id)
        .options(selectinload(TaskHistory.user))
        .order_by(TaskHistory.changed_at.desc())
    )
    result = await db.execute(stmt)
    history = result.scalars().all()
    return [
        {
            "id": h.id, "user_id": h.user_id,
            "user_name": h.user.full_name if h.user else None,
            "field": h.field, "old_value": h.old_value,
            "new_value": h.new_value, "changed_at": h.changed_at,
        }
        for h in history
    ]


# ---------------------------------------------------------------
#                       Отчёты
# ---------------------------------------------------------------
@router.get(
    "/reports/by-user",
    response_model=ReportResponse,
    dependencies=[Depends(require_role("manager", "admin"))],
)
async def report_by_user(
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Отчёт по производительности сотрудников за период."""
    period_end = datetime.now(timezone.utc).replace(tzinfo=None)
    period_start = period_end - timedelta(days=days)

    # Все исполнители
    users_result = await db.execute(
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.full_name)
    )
    users = users_result.scalars().all()

    items = []
    for u in users:
        total_stmt = select(func.count()).select_from(Task).where(
            and_(
                Task.assignee_id == u.id,
                Task.created_at >= period_start,
            )
        )
        completed_stmt = select(func.count()).select_from(Task).where(
            and_(
                Task.assignee_id == u.id,
                Task.created_at >= period_start,
                Task.status == TaskStatus.DONE,
            )
        )
        overdue_stmt = select(func.count()).select_from(Task).where(
            and_(
                Task.assignee_id == u.id,
                Task.deadline < datetime.now(timezone.utc).replace(tzinfo=None),
                Task.status != TaskStatus.DONE,
            )
        )

        total = (await db.execute(total_stmt)).scalar() or 0
        completed = (await db.execute(completed_stmt)).scalar() or 0
        overdue = (await db.execute(overdue_stmt)).scalar() or 0

        completion_rate = (completed / total * 100) if total > 0 else 0.0

        items.append(ReportItem(
            user_id=u.id,
            user_name=u.full_name,
            total_tasks=total,
            completed_tasks=completed,
            overdue_tasks=overdue,
            completion_rate=round(completion_rate, 1),
        ))

    return ReportResponse(
        period_start=period_start,
        period_end=period_end,
        items=items,
    )
