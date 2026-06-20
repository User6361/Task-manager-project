"""
Заполнение БД демонстрационными данными.

Создаёт:
- 3 роли (admin, manager, executor)
- 6 пользователей (1 админ, 1 руководитель, 4 исполнителя)
- 3 проекта
- 10 тегов
- 25 задач с разными статусами, приоритетами, дедлайнами
- Несколько комментариев и истории изменений

Учётные записи (логин / пароль):
    admin    / admin123
    manager  / manager123
    ivanov   / executor123
    petrov   / executor123
    sidorov  / executor123
    kuznetsov/ executor123
"""
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.database import AsyncSessionLocal, engine, Base
from app.models import (
    Role, User, Project, Tag, Task, TaskStatus, Comment,
    TaskHistory, Notification, NotificationType,
)
from app.security import hash_password
from app.services import calc_priority, calc_urgency_from_deadline


async def reset_database():
    """Сбросить и создать схему."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed():
    async with AsyncSessionLocal() as db:
        # Роли
        roles = [
            Role(code="admin",    name="Администратор",
                 description="Полный доступ к системе"),
            Role(code="manager",  name="Руководитель",
                 description="Постановка задач и контроль выполнения"),
            Role(code="executor", name="Исполнитель",
                 description="Выполнение назначенных задач"),
        ]
        db.add_all(roles)
        await db.commit()
        for r in roles:
            await db.refresh(r)
        role_admin = roles[0]
        role_manager = roles[1]
        role_executor = roles[2]

        # Пользователи
        users = [
            User(login="admin", password_hash=hash_password("admin123"),
                 full_name="Администратор Системный",
                 email="admin@example.ru", role_id=role_admin.id),
            User(login="manager_po_python", password_hash=hash_password("manager123"),
                 full_name="Арманова Мария Викторовна",
                 email="armanovapython@example.ru", role_id=role_manager.id),
            User(login="1ctop", password_hash=hash_password("executor123"),
                 full_name="Сидоренко Сергей Максимович",
                 email="sidorenko1c@example.ru", role_id=role_executor.id),
            User(login="petrov", password_hash=hash_password("executor123"),
                 full_name="Петров Алексей Викторович",
                 email="petrov@example.ru", role_id=role_executor.id),
            User(login="sidorov", password_hash=hash_password("executor123"),
                 full_name="Сидоров Дмитрий Николаевич",
                 email="sidorov@example.ru", role_id=role_executor.id),
            User(login="kuznetsova", password_hash=hash_password("executor123"),
                 full_name="Кузнецова Елена Сергеевна",
                 email="kuznetsova@example.ru", role_id=role_executor.id),
        ]
        db.add_all(users)
        await db.commit()
        for u in users:
            await db.refresh(u)
        admin, manager, ivanov, petrov, sidorov, kuznetsova = users

        # Теги
        tags = [
            Tag(name="срочно", color="#dc2626"),
            Tag(name="бэкенд", color="#2563eb"),
            Tag(name="фронтенд", color="#16a34a"),
            Tag(name="база данных", color="#9333ea"),
            Tag(name="документация", color="#888888"),
            Tag(name="дизайн", color="#ec4899"),
            Tag(name="тестирование", color="#ca8a04"),
            Tag(name="инфраструктура", color="#0891b2"),
            Tag(name="безопасность", color="#7c2d12"),
            Tag(name="оптимизация", color="#475569"),
        ]
        db.add_all(tags)
        await db.commit()
        for t in tags:
            await db.refresh(t)

        # Проекты
        projects = [
            Project(name="Корпоративный портал",
                    description="Разработка нового интранета компании",
                    owner_id=manager.id),
            Project(name="Мобильное приложение",
                    description="iOS и Android клиенты для клиентского сервиса",
                    owner_id=manager.id),
            Project(name="Внутренняя аналитика",
                    description="Дашборды и отчётность для руководства",
                    owner_id=manager.id),
        ]
        db.add_all(projects)
        await db.commit()
        for p in projects:
            await db.refresh(p)
        proj1, proj2, proj3 = projects

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Задачи (25 шт.) — миксованные статусы и сроки для демонстрации
        task_data = [
            # Корпоративный портал
            ("Спроектировать структуру БД пользователей", "Разработать ER-диаграмму с учётом ролевой модели",
             4, now + timedelta(days=2), TaskStatus.IN_PROGRESS, ivanov.id, [tags[3], tags[1]], proj1.id),
            ("Реализовать REST API авторизации", "JWT-токены, защита эндпоинтов",
             4, now + timedelta(days=5), TaskStatus.IN_PROGRESS, petrov.id, [tags[1], tags[8]], proj1.id),
            ("Сверстать главную страницу", "Адаптивная вёрстка, шапка, меню",
             3, now + timedelta(days=7), TaskStatus.TODO, kuznetsova.id, [tags[2], tags[5]], proj1.id),
            ("Написать модуль уведомлений", "Бэкенд + фронтенд интеграция",
             3, now + timedelta(days=10), TaskStatus.TODO, sidorov.id, [tags[1], tags[2]], proj1.id),
            ("Настроить CI/CD пайплайн", "GitLab CI + автоматические тесты",
             3, now + timedelta(days=14), TaskStatus.TODO, ivanov.id, [tags[7]], proj1.id),
            ("Подготовить документацию API", "OpenAPI + примеры использования",
             2, now + timedelta(days=20), TaskStatus.TODO, petrov.id, [tags[4]], proj1.id),
            ("Code review модуля авторизации", "Проверить безопасность, производительность",
             3, now + timedelta(days=3), TaskStatus.REVIEW, manager.id, [tags[8], tags[6]], proj1.id),
            ("Оптимизировать загрузку страниц", "Минификация, lazy-loading",
             2, now + timedelta(days=15), TaskStatus.TODO, kuznetsova.id, [tags[9], tags[2]], proj1.id),

            # Мобильное приложение
            ("Спроектировать дизайн экранов", "Figma макеты, design system",
             4, now + timedelta(days=4), TaskStatus.IN_PROGRESS, kuznetsova.id, [tags[5]], proj2.id),
            ("Реализовать экран входа iOS", "SwiftUI, биометрия",
             3, now + timedelta(days=8), TaskStatus.TODO, sidorov.id, [tags[2]], proj2.id),
            ("Реализовать экран входа Android", "Jetpack Compose",
             3, now + timedelta(days=8), TaskStatus.TODO, petrov.id, [tags[2]], proj2.id),
            ("Push-уведомления", "FCM + APNS интеграция",
             3, now + timedelta(days=12), TaskStatus.TODO, ivanov.id, [tags[1], tags[7]], proj2.id),
            ("Тестирование на устройствах", "Список устройств + тест-план",
             2, now + timedelta(days=25), TaskStatus.TODO, kuznetsova.id, [tags[6]], proj2.id),
            ("Оффлайн-режим", "Локальное хранение, синхронизация",
             3, now + timedelta(days=18), TaskStatus.TODO, sidorov.id, [tags[1]], proj2.id),
            ("Аналитика событий", "Метрики, воронки, retention",
             2, now + timedelta(days=22), TaskStatus.TODO, petrov.id, [tags[1]], proj2.id),

            # Внутренняя аналитика
            ("Настроить хранилище данных", "ETL пайплайн, инкрементальная загрузка",
             4, now + timedelta(days=6), TaskStatus.IN_PROGRESS, ivanov.id, [tags[3], tags[7]], proj3.id),
            ("Дашборд по продажам", "BI-инструмент, визуализации",
             3, now + timedelta(days=11), TaskStatus.TODO, kuznetsova.id, [tags[2]], proj3.id),
            ("Отчёт по эффективности команды", "Еженедельный отчёт автоматически",
             2, now + timedelta(days=16), TaskStatus.TODO, sidorov.id, [tags[4]], proj3.id),
            ("Прогнозирование ключевых метрик", "ML-модель, базовая версия",
             3, now + timedelta(days=30), TaskStatus.TODO, petrov.id, [tags[1]], proj3.id),
            ("Интеграция с CRM", "Синхронизация данных клиентов",
             3, now + timedelta(days=20), TaskStatus.TODO, ivanov.id, [tags[1]], proj3.id),

            # Несколько выполненных
            ("Утвердить ТЗ на портал", "Согласовать с заказчиком",
             4, now - timedelta(days=10), TaskStatus.DONE, manager.id, [tags[4]], proj1.id),
            ("Закупить серверное оборудование", "Согласовать с инфраструктурой",
             3, now - timedelta(days=5), TaskStatus.DONE, admin.id, [tags[7]], proj1.id),
            ("Развернуть тестовый стенд", "Docker + базовая конфигурация",
             3, now - timedelta(days=3), TaskStatus.DONE, ivanov.id, [tags[7]], proj1.id),

            # Несколько просроченных (для демонстрации эскалации)
            ("Подготовить демо-презентацию", "Слайды + скрипт демонстрации",
             3, now - timedelta(days=2), TaskStatus.IN_PROGRESS, kuznetsova.id, [tags[4]], proj2.id),
            ("Провести аудит безопасности", "Внешний пентест",
             4, now - timedelta(days=1), TaskStatus.TODO, petrov.id, [tags[8]], proj1.id),
        ]

        for (title, desc, importance, deadline, status, assignee_id,
             task_tags_list, project_id) in task_data:
            urgency = calc_urgency_from_deadline(deadline)
            priority = calc_priority(importance, urgency)
            t = Task(
                title=title,
                description=desc,
                importance=importance,
                priority=priority,
                deadline=deadline,
                status=status,
                project_id=project_id,
                assignee_id=assignee_id,
                author_id=manager.id,
                tags=task_tags_list,
            )
            db.add(t)
        await db.commit()

        # Получим первые задачи и добавим к ним комментарии и историю
        result = await db.execute(select(Task).order_by(Task.id).limit(5))
        first_tasks = result.scalars().all()

        if first_tasks:
            t1 = first_tasks[0]
            db.add_all([
                Comment(task_id=t1.id, author_id=manager.id,
                        text="Иван, не забудь учесть требования по нагрузке."),
                Comment(task_id=t1.id, author_id=ivanov.id,
                        text="Принято, в течение дня подготовлю первый вариант."),
                Comment(task_id=t1.id, author_id=manager.id,
                        text="Хорошо. Обсудим завтра на стендапе."),
            ])

            t2 = first_tasks[1]
            db.add_all([
                Comment(task_id=t2.id, author_id=petrov.id,
                        text="Какой алгоритм хеширования использовать — bcrypt или argon2?"),
                Comment(task_id=t2.id, author_id=manager.id,
                        text="Bcrypt подойдёт, аргон2 пока избыточен."),
            ])

            db.add_all([
                TaskHistory(task_id=t1.id, user_id=ivanov.id,
                            field="status", old_value="todo", new_value="in_progress"),
                TaskHistory(task_id=t2.id, user_id=petrov.id,
                            field="status", old_value="todo", new_value="in_progress"),
            ])

        # Несколько уведомлений
        db.add_all([
            Notification(user_id=ivanov.id, task_id=first_tasks[0].id if first_tasks else None,
                         type=NotificationType.TASK_ASSIGNED,
                         message="Вам назначена задача «Спроектировать структуру БД пользователей»"),
            Notification(user_id=petrov.id, task_id=first_tasks[1].id if len(first_tasks) > 1 else None,
                         type=NotificationType.TASK_ASSIGNED,
                         message="Вам назначена задача «Реализовать REST API авторизации»"),
            Notification(user_id=manager.id,
                         type=NotificationType.TASK_OVERDUE,
                         message="Просрочена задача «Провести аудит безопасности»"),
        ])

        await db.commit()
        print("✓ Демо-данные загружены")
        print()
        print("Учётные записи:")
        print("  admin     / admin123      (администратор)")
        print("  manager   / manager123    (руководитель)")
        print("  ivanov    / executor123   (исполнитель)")
        print("  petrov    / executor123   (исполнитель)")
        print("  sidorov   / executor123   (исполнитель)")
        print("  kuznetsova/ executor123   (исполнитель)")


async def main():
    print("Сброс схемы БД...")
    await reset_database()
    print("Загрузка демо-данных...")
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
