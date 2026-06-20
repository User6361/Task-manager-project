"""
Точка входа приложения «Менеджер задач».

Запуск: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, users, projects, tasks, extras
from app.scheduler import start_scheduler, stop_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запуск планировщика при старте приложения."""
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Менеджер задач",
    description=(
        "REST API информационной системы «Менеджер задач». "
        "Дипломный проект Петросяна Э.Г., ГБПОУ МИК, 09.02.07."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# CORS — разрешаем фронтенду на любом порту обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение роутеров
API_V1 = "/api/v1"
app.include_router(auth.router, prefix=API_V1)
app.include_router(users.router, prefix=API_V1)
app.include_router(projects.router, prefix=API_V1)
app.include_router(tasks.router, prefix=API_V1)
app.include_router(extras.notif_router, prefix=API_V1)
app.include_router(extras.tags_router, prefix=API_V1)


@app.get("/")
async def root():
    return {
        "name": "Менеджер задач",
        "version": "1.0.0",
        "docs": "/docs",
        "api": API_V1,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
