"""
Pydantic-схемы для валидации входящих запросов и формирования ответов API.
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


from app.models import TaskStatus, NotificationType

# ============== ОБЩИЕ ==============
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    login: str
    password: str


# ============== ROLE ==============
class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: Optional[str] = None


# ============== USER ==============
class UserBase(BaseModel):
    login: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)
    email: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=4)
    role_id: int


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: RoleOut
    is_active: bool
    created_at: datetime


# ============== TAG ==============
class TagBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#888888", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    pass


class TagOut(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ============== PROJECT ==============
class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime


# ============== COMMENT ==============
class CommentCreate(BaseModel):
    text: str = Field(min_length=1)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    author_name: Optional[str] = None
    text: str
    created_at: datetime


# ============== TASK ==============
class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    importance: int = Field(default=2, ge=1, le=4)
    deadline: Optional[datetime] = None
    project_id: int
    @field_validator("deadline", mode="before")
    @classmethod
    def normalize_deadline(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Парсим ISO формат с Z
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v



class TaskCreate(TaskBase):
    assignee_id: Optional[int] = None  # если None — будет автораспределение
    parent_task_id: Optional[int] = None
    tag_ids: List[int] = []



class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    importance: Optional[int] = Field(default=None, ge=1, le=4)
    deadline: Optional[datetime] = None
    assignee_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    @field_validator("deadline", mode="before")
    @classmethod
    def normalize_deadline(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Парсим ISO формат с Z
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    importance: int
    priority: int
    deadline: Optional[datetime]
    project_id: int
    assignee_id: Optional[int]
    assignee_name: Optional[str] = None
    author_id: int
    author_name: Optional[str] = None
    parent_task_id: Optional[int]
    is_escalated: bool
    created_at: datetime
    updated_at: datetime
    tags: List[TagOut] = []


class TaskHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: Optional[str] = None
    field: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_at: datetime


# ============== NOTIFICATION ==============
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    message: str
    task_id: Optional[int]
    is_read: bool
    created_at: datetime


# ============== АВТОРАСПРЕДЕЛЕНИЕ ==============
class AutoAssignRequest(BaseModel):
    task_id: int


class AutoAssignResponse(BaseModel):
    task_id: int
    assignee_id: int
    assignee_name: str
    weight: float
    candidates: List[dict]  # подробности по всем кандидатам — для отладки/демо


# ============== ОТЧЁТЫ ==============
class ReportItem(BaseModel):
    user_id: int
    user_name: str
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    completion_rate: float


class ReportResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    items: List[ReportItem]
