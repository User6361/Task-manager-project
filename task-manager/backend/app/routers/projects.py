"""Управление проектами."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Project, User
from app.schemas import ProjectOut, ProjectCreate
from app.security import get_current_user, require_role

router = APIRouter(prefix="/projects", tags=["Проекты"])


@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Список всех проектов."""
    result = await db.execute(select(Project).order_by(Project.name))
    return result.scalars().all()


@router.post(
    "/",
    response_model=ProjectOut,
    dependencies=[Depends(require_role("manager", "admin"))],
)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Создание нового проекта. Доступно руководителю и администратору."""
    project = Project(
        name=payload.name,
        description=payload.description,
        owner_id=current.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Получение проекта по ID."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    return project
