from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from app.schemas import ProjectResponse,ProjectCreate,ProjectUpdate,TaskResponse

router = APIRouter(prefix="/projects", tags=["Projects"])
DB = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=list[ProjectResponse])
def read_projects(db: DB):
    return crud.get_projects(db)

@router.get("/{project_id}", response_model=ProjectResponse)
def read_project(project_id: int, db: DB):
    project = crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: DB):
    if crud.get_project_by_name(db, data.name):
        raise HTTPException(400, "Project name already exists")
    return crud.create_project(db, data)

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: DB):
    project = crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    if data.name is not None:
        existing = crud.get_project_by_name(db, data.name)
        if existing is not None and existing.id != project_id:
            raise HTTPException(400, "Project name already exists")

    return crud.update_project(db, project, data)

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: DB):
    project = crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(404,"Project not found")
    if crud.get_project_tasks(db, project_id):
        raise HTTPException(400,"Project has tasks")
    crud.delete_project(db, project)
    return Response(status_code=204)

@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
def read_project_tasks(project_id: int, db: DB):
    if crud.get_project(db, project_id) is None:
        raise HTTPException(404,"Project not found")
    return crud.get_project_tasks(db, project_id)
