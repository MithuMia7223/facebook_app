from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from ..db import get_db
    from ..models import User
    from ..auth import read_current_user, read_current_user_allow_inactive
except ImportError:
    from db import get_db
    from models import User
    from auth import read_current_user, read_current_user_allow_inactive

router = APIRouter(prefix="/setting", tags=["setting"])


@router.post("/deactivate")
def deactive_account(
    current_user: User = Depends(read_current_user), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = 0
    db.commit()
    return {"message": "Account deactivated"}


@router.post("/reactivate")
def reactivate_account(
    current_user: User = Depends(read_current_user_allow_inactive),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = 1
    db.commit()
    return {"message": "Account reactivated"}


@router.delete("/delete")
def delete_accoutn(
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_deleted = True
    db.commit()

    return {"message": "Account deleted"}
