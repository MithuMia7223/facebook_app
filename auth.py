from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import secrets

try:
    from .db import get_db
    from .models import User
except ImportError:
    from db import get_db
    from models import User

security = HTTPBasic()


def read_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not secrets.compare_digest(user.password, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if user.is_deleted:
        raise HTTPException(
            status_code=403,
            detail="User account deleted",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is deactivated",
        )

    return user


def read_current_user_allow_inactive(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not secrets.compare_digest(user.password, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if user.is_deleted:
        raise HTTPException(
            status_code=403,
            detail="User account deleted",
        )

    return user
