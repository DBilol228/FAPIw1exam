from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import settings
from app import crud

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
DB = Annotated[Session, Depends(get_db)]

def credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DB,
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp"]}
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise credentials_error()
    user = crud.get_user(db, user_id)
    if user is None or not user.is_active:
        raise credentials_error()
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

AdminUser = Annotated[User, Depends(require_admin)]