from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base,engine
from app.routers import projects, employees, tasks, users
from fastapi import Depends
from app.dependencies import get_current_user
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="TaskManager",lifespan=lifespan)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")

app.include_router(users.router)
app.include_router(projects.router, dependencies=[Depends(get_current_user)])
app.include_router(employees.router, dependencies=[Depends(get_current_user)])
app.include_router(tasks.router, dependencies=[Depends(get_current_user)])
