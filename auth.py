from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

try:
    from .db import get_db
    from .models import User
except ImportError:
    from db import get_db
    from models import User

router = APIRouter()
security = HTTPBasic()


def read_current_user(
    credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or user.password != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user
