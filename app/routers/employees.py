from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import *
from app.dependencies import AdminUser

router = APIRouter(prefix="/employees", tags=["Employees"])
DB = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=list[EmployeeResponse])
def read_employees(
    db: DB,
    search: str | None = None,
    position: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    return crud.get_employees(db, search, position, limit, offset)

@router.get("/{employee_id}", response_model=EmployeeResponse)
def read_employee(employee_id: int, db: DB):
    employee = crud.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(404,"Employee not found")
    return employee

@router.post("/", response_model=EmployeeResponse, status_code=201)
def create_employee(data: EmployeeCreate, db: DB, admin: AdminUser):
    if crud.get_employee_by_email(db, data.email):
        raise HTTPException(400, "Email already exists")
    return crud.create_employee(db, data)

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, data: EmployeeUpdate, db: DB, admin: AdminUser):
    employee = crud.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(404, "Employee not found")
    existing = crud.get_employee_by_email(db, data.email)
    if existing is not None and existing.id != employee_id:
        raise HTTPException(400, "Email already exists")
    return crud.update_employee(db, employee, data)

@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: DB, admin: AdminUser):
    employee = crud.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(404, "Employee not found")
    if crud.get_employee_tasks(db, employee_id):
        raise HTTPException(400, "Employee has tasks")
    crud.delete_employee(db, employee)
    return Response(status_code=204)

@router.get("/{employee_id}/tasks", response_model=list[TaskResponse])
def read_employee_tasks(employee_id: int, db: DB):
    if crud.get_employee(db, employee_id) is None:
        raise HTTPException(404, "Employee not found")
    return crud.get_employee_tasks(db, employee_id)