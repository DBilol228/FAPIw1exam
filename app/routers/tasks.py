from app import crud
from app.database import get_db
from app.schemas import *

from datetime import date
from typing import Annotated
from fastapi import APIRouter,Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.dependencies import AdminUser

router = APIRouter(prefix="/tasks",tags=["Tasks"])
DB = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=list[TaskResponse])
def read_tasks(
    db: DB,
    search: str | None = None,
    status: TaskStatus | None = None,
    priority: int | None = Query(default=None, ge=1, le=5),
    project_id: int | None = None,
    employee_id: int | None = None,
    deadline_before: date | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    return crud.get_tasks(
        db,
        search=search,
        status=status,
        priority=priority,
        project_id=project_id,
        employee_id=employee_id,
        deadline_before=deadline_before,
        limit=limit,
        offset=offset
    )

@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: int, db: DB):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task

@router.post("/",response_model=TaskResponse, status_code=201)
def create_task(data: TaskCreate, db: DB, admin: AdminUser):
    if crud.get_project(db, data.project_id) is None:
        raise HTTPException(404, "Project not found")
    if data.employee_id is not None:
        employee = crud.get_employee(db, data.employee_id)
        if employee is None:
            raise HTTPException(404, "Employee not found")
        if not employee.is_active:
            raise HTTPException(400, "Employee is inactive")
    return crud.create_task(db, data)

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskCreate, db: DB):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    if crud.get_project(db, data.project_id) is None:
        raise HTTPException(404, "Project not found")
    if data.employee_id is not None:
        employee = crud.get_employee(db, data.employee_id)
        if employee is None:
            raise HTTPException(404, "Employee not found")
        if not employee.is_active:
            raise HTTPException(400, "Employee is inactive")
    return crud.update_task(db, task, data)

@router.patch("/{task_id}", response_model=TaskResponse)
def patch_task(task_id: int, data: TaskUpdate, db: DB):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    if data.project_id is not None:
        if crud.get_project(db, data.project_id) is None:
            raise HTTPException(404, "Project not found")
    if data.employee_id is not None:
        employee = crud.get_employee(db, data.employee_id)
        if employee is None:
            raise HTTPException(404, "Employee not found")
        if not employee.is_active:
            raise HTTPException(400, "Employee is inactive")
    return crud.update_task(db, task, data, partial=True)

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: DB, admin: AdminUser):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(404,"Task not found")
    crud.delete_task(db, task)
    return Response(status_code=204)

@router.patch("/{task_id}/assign", response_model=TaskResponse)
def assign_task(task_id: int, data: TaskAssign, db: DB, admin: AdminUser):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(404,"Task not found")
    if data.employee_id is not None:
        employee = crud.get_employee(db, data.employee_id)
        if employee is None:
            raise HTTPException(404,"Employee not found")
        if not employee.is_active:
            raise HTTPException(400,"Employee is inactive")
    return crud.assign_task(db, task, data.employee_id)

@router.patch("/{task_id}/status",response_model=TaskResponse)
def update_task_status(task_id: int, data: TaskStatusUpdate,db: DB):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return crud.update_task_status(db, task, data.status)