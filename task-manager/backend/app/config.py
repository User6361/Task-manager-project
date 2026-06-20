"""
Конфигурация приложения «Менеджер задач».

По умолчанию используется SQLite (для быстрого локального запуска).
Для production-режима достаточно установить переменную окружения
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # База данных
    database_url: str = Field(
        default="sqlite+aiosqlite:///./taskmanager.db",
        description="URL подключения к БД (SQLite по умолчанию, PostgreSQL для production)"
    )

    # JWT
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-OPENSSL-RAND-HEX-32",
        description="Секретный ключ для подписи JWT-токенов"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 часа

    # Параметры алгоритма автораспределения (формула 2.1 из главы 2)
    autodist_alpha: float = 1.0   # вес количества задач
    autodist_beta: float = 0.5    # вес суммарного приоритета
    autodist_gamma: float = 2.0   # вес близости дедлайнов

    # Веса формулы расчёта приоритета (формула 2.3)
    priority_k_importance: float = 0.5
    priority_k_urgency: float = 0.5

    # Планировщик
    scheduler_check_interval_minutes: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
