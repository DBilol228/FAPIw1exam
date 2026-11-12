from pydantic import BaseModel,ConfigDict,EmailStr,Field,model_validator
from datetime import datetime,date
from typing import Literal

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None

class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    created_at: datetime

class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr = Field(max_length=150)
    position: str | None = Field(default=None, max_length=100)
    is_active: bool = True

class EmployeeUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr = Field(max_length=150)
    position: str | None = Field(default=None, max_length=100)
    is_active: bool = True

class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    position: str | None
    is_active: bool
    created_at: datetime

TaskStatus = Literal["todo", "in_progress", "done"]

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "todo"
    priority: int = Field(ge=1, le=5)
    deadline: date | None = None
    project_id: int
    employee_id: int | None = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: int
    deadline: date | None
    created_at: datetime
    project_id: int
    employee_id: int | None

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    deadline: date | None = None
    project_id: int | None = None
    employee_id: int | None = None
    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field in ("title", "status", "priority", "project_id"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self

class TaskAssign(BaseModel):
    employee_id: int | None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus