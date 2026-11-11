from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Project,Employee,Task
from app.schemas import *
from sqlalchemy import select
from datetime import date

def get_projects(db: Session):
    statement = select(Project).order_by(Project.id)
    return db.scalars(statement).all()

def get_project(db: Session, project_id: int):
    statement = select(Project).where(Project.id == project_id)
    return db.scalar(statement)

def get_project_by_name(db: Session, name: str):
    statement = select(Project).where(Project.name == name)
    return db.scalar(statement)

def create_project(db: Session, data: ProjectCreate):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def update_project(db: Session,project: Project,data: ProjectUpdate):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project

def delete_project(db: Session, project: Project):
    db.delete(project)
    db.commit()

def get_project_tasks(db: Session, project_id: int):
    statement = (select(Task).where(Task.project_id == project_id).order_by(Task.id))
    return db.scalars(statement).all()

def get_employees(db: Session,search: str | None = None,position: str | None = None,limit: int = 10,offset: int = 0):
    statement = select(Employee)
    if search:
        statement = statement.where(Employee.full_name.ilike(f"%{search}%"))
    if position is not None:
        statement = statement.where(Employee.position == position)
    statement = statement.order_by(Employee.id).limit(limit).offset(offset)
    return db.scalars(statement).all()

def get_employee(db: Session, employee_id: int):
    statement = select(Employee).where(Employee.id == employee_id)
    return db.scalar(statement)

def get_employee_by_email(db: Session, email: str):
    statement = select(Employee).where(Employee.email == email)
    return db.scalar(statement)

def create_employee(db: Session, data: EmployeeCreate):
    employee = Employee(**data.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee

def update_employee(db: Session,employee: Employee,data: EmployeeUpdate):
    for field, value in data.model_dump().items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee

def get_employee_tasks(db: Session, employee_id: int):
    statement = (
        select(Task)
        .where(Task.employee_id == employee_id)
        .order_by(Task.id)
    )
    return db.scalars(statement).all()

def delete_employee(db: Session, employee: Employee):
    db.delete(employee)
    db.commit()

