from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

try:
    from ..db import get_db
    from ..models import User, friend_table
    from ..dtos import UserCreate, UserUpdate, UserGetMeResponse
    from ..auth import read_current_user
except ImportError:
    from db import get_db
    from models import User, friend_table
    from dtos import UserCreate, UserUpdate, UserGetMeResponse
    from auth import read_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserGetMeResponse)
def get_me(
    current_user: User = Depends(read_current_user),
):
    return current_user


@router.get("/{id}", response_model=UserGetMeResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/username/{username}", response_model=UserGetMeResponse)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{id}", response_model=UserGetMeResponse)
def update_user(
    id: int,
    data: UserUpdate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if data.name:
        user.name = data.name
    if data.bio:
        user.bio = data.bio

    db.commit()
    db.refresh(user)
    return user


@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = User(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/friends/{friend_id}")
def add_friend(
    id: int,
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if id == friend_id:
        raise HTTPException(status_code=400, detail="You cannot add yourself")
    user = db.query(User).filter(User.id == id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    if not user or not friend:
        raise HTTPException(status_code=404, detail="User not found")
    if friend not in user.friends:
        user.friends.append(friend)
        friend.friends.append(user)
        db.commit()
    return {"message": "Friend added"}


@router.get("/{id}/friends")
def get_friends(
    id: int,
    limit: int = Query(10),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    total = (
        db.query(User)
        .join(friend_table, User.id == friend_table.c.friend_id)
        .filter(friend_table.c.user_id == id)
        .count()
    )
    friends = (
        db.query(User)
        .join(friend_table, User.id == friend_table.c.friend_id)
        .filter(friend_table.c.user_id == id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "limit": limit, "offset": offset, "data": friends}


@router.delete("/{id}/friends/{friend_id}")
def remove_friend(
    id: int,
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.id == id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    if not user or not friend:
        raise HTTPException(status_code=404, detail="User not found")
    if friend in user.friends:
        user.friends.remove(friend)
        friend.friends.remove(user)
        db.commit()
    return {"message": "Friend removed"}
