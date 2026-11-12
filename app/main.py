from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base,engine
from app.routers import projects, employees, tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="TaskManager",lifespan=lifespan)

app.include_router(projects.router)
app.include_router(employees.router)
app.include_router(tasks.router)