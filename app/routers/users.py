from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from app.dependencies import CurrentUser, AdminUser
from app.schemas import RegisterRequest, UserResponse, TokenResponse
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(tags=["Authentication"])
DB = Annotated[Session, Depends(get_db)]

@router.post("/auth/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: DB):
    if crud.get_user_by_username(db, data.username) is not None:
        raise HTTPException(409, "Username already exists")
    try:
        return crud.create_user(db, data.username, hash_password(data.password))
    except IntegrityError:
        raise HTTPException(409, "Username already exists")

@router.post("/auth/login", response_model=TokenResponse)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    user = crud.get_user_by_username(db, form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(403, "Account is inactive")
    return TokenResponse(access_token=create_access_token(user.id))

@router.get("/users/me", response_model=UserResponse)
def read_me(current_user: CurrentUser):
    return current_user

@router.get("/admin/users", response_model=list[UserResponse])
def list_users(db: DB, admin: AdminUser):
    return crud.get_users(db)
