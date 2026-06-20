"""
Сервисы алгоритмов автоматизации.

Реализуют:
- Алгоритм автоматического распределения задач (формула 2.1, рисунок 2.4)
- Расчёт приоритета задачи (формула 2.3, рисунок 2.5)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, UTC
import logging


from app.config import settings
from app.models import User, Task, TaskStatus, Role


# ---------------------------------------------------------------
#                   РАСЧЁТ ПРИОРИТЕТА ЗАДАЧИ
# ---------------------------------------------------------------
def calc_urgency_from_deadline(deadline: Optional[datetime]) -> int:
    """
    Определение срочности задачи (1..4) по близости крайнего срока.

    - Срок просрочен или менее 1 дня → 4
    - До 3 дней                       → 3
    - До 7 дней                       → 2
    - Более 7 дней или нет срока      → 1
    """
    if deadline is None:
        return 1
    
    
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    deadline = deadline.replace(tzinfo=None)
    days_left = (deadline - now).total_seconds() / 86400
    
    


    if days_left < 1:
        return 4
    elif days_left < 3:
        return 3
    elif days_left < 7:
        return 2
    return 1


def calc_priority(importance: int, urgency: int) -> int:
    """
    Расчёт приоритета задачи по формуле 2.3:
        P = round(I * k_i + S * k_s)
    Возвращаемое значение лежит в диапазоне 1..4.
    """
    raw = (
        importance * settings.priority_k_importance
        + urgency * settings.priority_k_urgency
    )
    p = round(raw)
    return max(1, min(4, p))


def calc_task_priority(task: Task) -> int:
    """Удобная обёртка: рассчитать приоритет конкретной задачи."""
    urgency = calc_urgency_from_deadline(task.deadline)
    return calc_priority(task.importance, urgency)


# ---------------------------------------------------------------
#         АЛГОРИТМ АВТОРАСПРЕДЕЛЕНИЯ (формула 2.1)
# ---------------------------------------------------------------
async def calc_user_weight(
    db: AsyncSession, user_id: int
) -> Tuple[float, dict]:
    """
    Расчёт веса исполнителя по формуле 2.1:
        W = α·N + β·P + γ·D
    где:
        N — количество активных задач
        P — суммарный приоритет активных задач
        D — показатель близости крайних сроков (формула 2.2)
    """
    stmt = select(Task).where(
        and_(
            Task.assignee_id == user_id,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW]),
        )
    )
    result = await db.execute(stmt)
    active_tasks = result.scalars().all()

    n = len(active_tasks)
    p = sum(t.priority for t in active_tasks)

    # D = Σ (1 / max(t_i, 1)) — формула 2.2
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    d = 0.0
    for t in active_tasks:
        if t.deadline is None:
            continue
        days_left = max((t.deadline - now).total_seconds() / 86400, 1.0)
        d += 1.0 / days_left

    weight = (
        settings.autodist_alpha * n
        + settings.autodist_beta * p
        + settings.autodist_gamma * d
    )

    details = {
        "user_id": user_id,
        "active_tasks_count": n,
        "total_priority": p,
        "deadline_pressure": round(d, 3),
        "weight": round(weight, 3),
    }
    return weight, details


async def auto_assign_task(
    db: AsyncSession, task: Task
) -> Tuple[Optional[User], List[dict]]:
    """
    Автоматическое распределение задачи между исполнителями.

    Реализует алгоритм по блок-схеме (рисунок 2.4):
    1. Получить активных исполнителей
    2. Рассчитать веса
    3. Выбрать с минимальным весом
    4. При равенстве — кто дольше всего не получал задач

    Возвращает (выбранный исполнитель, список деталей по всем кандидатам)
    """
    # Шаг 1: получить активных пользователей с ролью «исполнитель» или «руководитель»
    stmt = (
        select(User)
        .join(Role)
        .where(
            and_(
                User.is_active.is_(True),
                Role.code.in_(["executor", "manager"]),
            )
        )
    )
    result = await db.execute(stmt)
    candidates = list(result.scalars().all())

    if not candidates:
        return None, []

    # Шаг 2: рассчитать веса всех кандидатов
    candidates_with_weights = []
    for u in candidates:
        weight, details = await calc_user_weight(db, u.id)
        details["user_name"] = u.full_name
        candidates_with_weights.append((u, weight, details))

    # Шаг 3: выбрать минимальный вес
    min_weight = min(cw[1] for cw in candidates_with_weights)
    finalists = [cw for cw in candidates_with_weights if cw[1] == min_weight]

    if len(finalists) == 1:
        chosen_user, chosen_weight, _ = finalists[0]
    else:
        # Шаг 4: кто дольше всего не получал задач
        # Получаем дату последнего назначения для каждого финалиста
        finalists_with_last = []
        for user, weight, det in finalists:
            stmt = (
                select(func.max(Task.created_at))
                .where(Task.assignee_id == user.id)
            )
            r = await db.execute(stmt)
            last_assigned = r.scalar()
            finalists_with_last.append((user, weight, det, last_assigned))

        # Сортируем: None (никогда не получал) — выше всех, затем по возрастанию даты
        finalists_with_last.sort(
            key=lambda x: (x[3] is not None, x[3] or datetime.min)
        )
        chosen_user, chosen_weight, _, _ = finalists_with_last[0]

    # Применяем назначение
    task.assignee_id = chosen_user.id

    # Все детали для возврата (отметить выбранного)
    all_details = []
    for u, w, det in candidates_with_weights:
        det["is_chosen"] = (u.id == chosen_user.id)
        all_details.append(det)

    return chosen_user, all_details
