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

def get_tasks(
    db: Session,
    search: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    deadline_before: date | None = None,
    limit: int = 10,
    offset: int = 0
):
    statement = select(Task)
    if search:
        statement = statement.where(Task.title.ilike(f"%{search}%"))
    if status is not None:
        statement = statement.where(Task.status == status)
    if priority is not None:
        statement = statement.where(Task.priority == priority)
    if project_id is not None:
        statement = statement.where(Task.project_id == project_id)
    if employee_id is not None:
        statement = statement.where(Task.employee_id == employee_id)
    if deadline_before is not None:
        statement = statement.where(Task.deadline < deadline_before)
    statement = (
        statement.order_by(Task.id)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(statement).all()

def get_task(db: Session, task_id: int):
    statement = select(Task).where(Task.id == task_id)
    return db.scalar(statement)

def create_task(db: Session, data: TaskCreate):
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def update_task(
    db: Session,
    task: Task,
    data: TaskCreate | TaskUpdate,
    *,
    partial: bool = False
):
    values = data.model_dump(exclude_unset=partial)
    for field, value in values.items():
        setattr(task,field,value)
    db.commit()
    db.refresh(task)
    return task

def assign_task(db: Session, task: Task, employee_id: int|None):
    task.employee_id = employee_id
    db.commit()
    db.refresh(task)
    return task

def update_task_status(db: Session, task: Task, status: str):
    task.status = status
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task: Task):
    db.delete(task)
    db.commit()