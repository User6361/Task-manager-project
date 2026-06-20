# Информационная система «Менеджер задач»

Дипломный проект Петросяна Эдуарда Гарниковича.
ГБПОУ МИК, специальность 09.02.07.

Стек: **FastAPI + Vue.js + PostgreSQL**.

---

## Способы запуска

### Вариант 1 — Простой (SQLite, без Docker)

Подойдёт для быстрого знакомства с системой и снятия скриншотов.
Требования: Python 3.10+, Node.js 18+.

#### 1. Запуск бэкенда

```bash
cd backend
python -m venv venv
source venv/bin/activate         # Linux/Mac
# venv\Scripts\activate          # Windows

pip install -r requirements.txt

# Заполнение БД демо-данными (создаст файл taskmanager.db)
python -m app.seed

# Запуск API
uvicorn app.main:app --reload --port 8000
```

API будет доступен на `http://localhost:8000`.
Документация Swagger: `http://localhost:8000/docs`.

#### 2. Запуск фронтенда (в отдельном терминале)

```bash
cd frontend
npm install
npm run dev
```

Фронтенд будет доступен на `http://localhost:5173`.

---

### Вариант 2 — Production (Docker Compose, PostgreSQL)

Полностью изолированный запуск с PostgreSQL — соответствует архитектуре,
описанной в Главе 2 пояснительной записки.

Требования: Docker, Docker Compose.

```bash
docker compose up --build
```

После сборки и старта (~1 минута):
- Фронтенд: `http://localhost:8080`
- API: `http://localhost:8000`
- БД PostgreSQL: `localhost:5432` (`taskmanager` / `taskmanager_pass`)

Остановка: `docker compose down`.
Сброс БД: `docker compose down -v`.

---

## Демонстрационные учётные записи

После выполнения сидинга в системе автоматически создаются:

| Логин        | Пароль        | Роль          |
|--------------|---------------|---------------|
| `admin`      | `admin123`    | Администратор |
| `manager`    | `manager123`  | Руководитель  |
| `ivanov`     | `executor123` | Исполнитель   |
| `petrov`     | `executor123` | Исполнитель   |
| `sidorov`    | `executor123` | Исполнитель   |
| `kuznetsova` | `executor123` | Исполнитель   |

Также создаётся 3 проекта, 10 тегов, 25 задач (включая просроченные —
для демонстрации эскалации) и набор комментариев и истории изменений.

---

## Что посмотреть на скриншотах

1. **Экран входа** (`/login`) — логин с быстрыми кнопками демо-аккаунтов
2. **Канбан-доска** (`/board`) — все 4 статуса с задачами, бейджи приоритетов,
   маркеры просрочек
3. **Список задач** (`/tasks`) — табличный вид с фильтрами по проекту/статусу
4. **Детальная страница задачи** (`/tasks/1`) — описание, теги, история,
   комментарии. **Главное** — нажать «Автораспределение»: появится таблица
   с расчётом веса W = α·N + β·P + γ·D для всех кандидатов.
5. **Создание задачи** (на канбан-доске «+ Новая задача») — модалка с галкой
   «Автоматическое распределение исполнителя» и пояснением формулы.
6. **Проекты** (`/projects`) — карточки проектов со статистикой
   (всего/в работе/готово/просрочено)
7. **Отчёты** (`/reports`, доступно руководителю и админу) — таблица
   эффективности сотрудников с прогресс-барами
8. **Пользователи** (`/users`, только админ) — управление учётными записями

---

## Структура проекта

```
task-manager/
├── backend/
│   ├── app/
│   │   ├── routers/         # REST endpoints (auth, users, projects, tasks, extras)
│   │   ├── models.py        # ORM-модели (9 сущностей из главы 2)
│   │   ├── schemas.py       # Pydantic-схемы
│   │   ├── services.py      # Алгоритмы (автораспределение, приоритет)
│   │   ├── scheduler.py     # APScheduler — эскалация, напоминания
│   │   ├── security.py      # JWT, bcrypt, проверка ролей
│   │   ├── seed.py          # Заполнение демо-данными
│   │   └── main.py          # Точка входа FastAPI
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/           # 8 страниц (LoginView, BoardView, TasksView, ...)
│   │   ├── components/      # TaskCard, TaskFormModal
│   │   ├── stores/          # Pinia store (auth)
│   │   ├── router/          # Vue Router
│   │   ├── api/             # axios-клиент
│   │   └── assets/          # стили
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Реализованные функции автоматизации (соответствие главе 2)

- **Автоматическое распределение задач** (формула 2.1, рисунок 2.4) —
  при создании задачи без `assignee_id` бэкенд выбирает наименее
  загруженного исполнителя по формуле `W = α·N + β·P + γ·D`.
  Просмотреть детали расчёта можно на странице задачи кнопкой
  «Автораспределение».

- **Расчёт приоритета** (формула 2.3, рисунок 2.5) — приоритет (1–4)
  рассчитывается автоматически на основе важности (задаёт автор) и
  срочности (вычисляется по дедлайну). Логика — в `services.calc_priority`.

- **Эскалация просроченных задач** — `scheduler.check_overdue_tasks`
  раз в 5 минут находит просроченные задачи и создаёт уведомления
  автору-руководителю с пометкой `is_escalated`.

- **Напоминания о приближении дедлайна** —
  `scheduler.check_approaching_deadlines` рассылает уведомления
  исполнителям за 24 часа до дедлайна (с защитой от повторов).

- **Повторяющиеся задачи** — `scheduler.process_recurring_rules`
  обрабатывает правила из таблицы `recurring_rules` и создаёт
  новые задачи по расписанию.

- **RBAC** (рисунок 2.6) — три роли (executor/manager/admin),
  проверка доступа через `security.require_role(...)` на каждом
  защищённом эндпоинте.

---

## API

Документация Swagger автоматически генерируется FastAPI и доступна
на `/docs`. Ключевые эндпоинты:

```
POST   /api/v1/auth/login          # Вход (JWT)
GET    /api/v1/auth/me             # Текущий пользователь

GET    /api/v1/tasks/              # Список задач (с фильтрами)
POST   /api/v1/tasks/              # Создание (с автораспределением)
GET    /api/v1/tasks/{id}          # Детали
PATCH  /api/v1/tasks/{id}          # Изменение
DELETE /api/v1/tasks/{id}          # Удаление
GET    /api/v1/tasks/board/view    # Канбан-доска

POST   /api/v1/tasks/auto-assign/{id}    # Принудительное автораспределение
GET    /api/v1/tasks/{id}/comments       # Комментарии
POST   /api/v1/tasks/{id}/comments       # Добавить комментарий
GET    /api/v1/tasks/{id}/history        # История изменений
GET    /api/v1/tasks/reports/by-user     # Отчёт по пользователям

GET    /api/v1/projects/           # Проекты
POST   /api/v1/projects/           # Создание проекта

GET    /api/v1/users/              # Пользователи
POST   /api/v1/users/              # Создание (admin)
PATCH  /api/v1/users/{id}          # Изменение (admin)
GET    /api/v1/users/roles/        # Список ролей

GET    /api/v1/notifications/      # Уведомления текущего пользователя
POST   /api/v1/notifications/{id}/read

GET    /api/v1/tags/               # Теги
POST   /api/v1/tags/               # Создание (manager/admin)
```

---

## Сброс данных

Удалить файл `backend/taskmanager.db` (для SQLite) или выполнить
`docker compose down -v` (для PostgreSQL), затем заново выполнить
`python -m app.seed`.
