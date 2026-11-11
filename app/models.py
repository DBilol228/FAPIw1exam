from sqlalchemy import String,Integer,Text,Boolean,DateTime,Date,ForeignKey
from .database import Base
from sqlalchemy.orm import Mapped, mapped_column,relationship
from datetime import datetime,date

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150),unique=True)
    description: Mapped[str | None] = mapped_column(Text,nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.now)
    tasks = relationship("Task",back_populates="project")

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150),unique=True)
    position: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    tasks = relationship("Task", back_populates="employee")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text,nullable=True)
    status: Mapped[str] = mapped_column(String(20),default="todo")
    priority: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[date | None] = mapped_column(Date,nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.now)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"),nullable=True)
    project = relationship("Project",back_populates="tasks")
    employee = relationship("Employee",back_populates="tasks")