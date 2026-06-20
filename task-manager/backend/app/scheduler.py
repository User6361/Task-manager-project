"""
Планировщик фоновых задач автоматизации.

Реализует функции из подразделов 1.4 и 2.4:
- Эскалация просроченных задач руководителю
- Напоминания о приближении дедлайнов
- Генерация повторяющихся задач по расписанию
"""
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import (
    Task, TaskStatus, User, Role, Notification, NotificationType,
    RecurringRule,
)
from app.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def check_overdue_tasks():
    """
    Эскалация просроченных задач.
    Запускается каждые 5 минут (по умолчанию).
    """
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        stmt = (
            select(Task)
            .where(
                and_(
                    Task.deadline.isnot(None),
                    Task.deadline < now,
                    Task.status != TaskStatus.DONE,
                    Task.is_escalated.is_(False),
                )
            )
            .options(selectinload(Task.author))
        )
        result = await db.execute(stmt)
        overdue = result.scalars().all()

        for task in overdue:
            # Уведомление автору задачи (руководителю)
            notif = Notification(
                user_id=task.author_id,
                task_id=task.id,
                type=NotificationType.TASK_OVERDUE,
                message=(
                    f"Просрочена задача «{task.title}». "
                    f"Срок истёк {task.deadline.strftime('%Y-%m-%d %H:%M')}"
                ),
            )
            db.add(notif)
            task.is_escalated = True
            logger.info(f"Эскалация задачи #{task.id}: «{task.title}»")

        if overdue:
            await db.commit()
            logger.info(f"Эскалировано задач: {len(overdue)}")


async def check_approaching_deadlines():
    """
    Напоминания о приближении дедлайнов (за 24 часа).
    """
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        threshold = now + timedelta(hours=24)

        stmt = (
            select(Task)
            .where(
                and_(
                    Task.deadline.isnot(None),
                    Task.deadline > now,
                    Task.deadline <= threshold,
                    Task.status != TaskStatus.DONE,
                    Task.assignee_id.isnot(None),
                )
            )
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        for task in tasks:
            # Проверим, не было ли уведомления за последние 12 часов
            recent_check = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.task_id == task.id,
                        Notification.user_id == task.assignee_id,
                        Notification.type == NotificationType.DEADLINE_APPROACHING,
                        Notification.created_at > now - timedelta(hours=12),
                    )
                )
            )
            if recent_check.scalar_one_or_none():
                continue  # уже уведомляли

            notif = Notification(
                user_id=task.assignee_id,
                task_id=task.id,
                type=NotificationType.DEADLINE_APPROACHING,
                message=(
                    f"Срок задачи «{task.title}» истекает "
                    f"{task.deadline.strftime('%Y-%m-%d %H:%M')}"
                ),
            )
            db.add(notif)

        if tasks:
            await db.commit()


async def process_recurring_rules():
    """
    Генерация задач по правилам повторения.
    """
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        stmt = (
            select(RecurringRule)
            .where(
                and_(
                    RecurringRule.is_active.is_(True),
                    RecurringRule.next_run <= now,
                )
            )
            .options(selectinload(RecurringRule.template_task))
        )
        result = await db.execute(stmt)
        rules = result.scalars().all()

        for rule in rules:
            template = rule.template_task
            if not template:
                continue

            new_task = Task(
                title=template.title,
                description=template.description,
                importance=template.importance,
                priority=template.priority,
                project_id=template.project_id,
                assignee_id=template.assignee_id,
                author_id=template.author_id,
                deadline=now + timedelta(days=7),  # типовой срок 7 дней
                status=TaskStatus.TODO,
            )
            db.add(new_task)

            # Простая логика: следующий запуск через 7 дней
            # (полноценный CRON-парсер вышел бы за пределы дипломного объёма)
            rule.next_run = now + timedelta(days=7)
            logger.info(f"Создана задача по правилу #{rule.id}")

        if rules:
            await db.commit()


def start_scheduler():
    """Запуск планировщика."""
    interval = settings.scheduler_check_interval_minutes
    scheduler.add_job(
        check_overdue_tasks,
        "interval",
        minutes=interval,
        id="check_overdue",
    )
    scheduler.add_job(
        check_approaching_deadlines,
        "interval",
        minutes=interval,
        id="check_deadlines",
    )
    scheduler.add_job(
        process_recurring_rules,
        "interval",
        minutes=interval,
        id="recurring_rules",
    )
    scheduler.start()
    logger.info("Планировщик запущен")


def stop_scheduler():
    """Остановка планировщика."""
    if scheduler.running:
        scheduler.shutdown()
