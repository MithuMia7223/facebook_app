from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import os
import uuid
import shutil


try:
    from ..db import get_db
    from ..models import User, FriendRequest
    from ..dtos import UserCreate, UserUpdate, UserGetResponse
    from ..auth import read_current_user
except:
    from db import get_db
    from models import User, FriendRequest
    from dtos import UserCreate, UserUpdate, UserGetResponse
    from auth import read_current_user

router = APIRouter(prefix="/users", tags=["Users"])

AVATAR_DIR = "uploads/avatars"
COVER_DIR = "uploads/covers"

os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)


@router.get("/me", response_model=UserGetResponse)
def get_my_profile(
    current_user: User = Depends(read_current_user), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "bio": user.bio,
        "location": user.location,
        "avatar_url": user.avatar_url,
        "cover_url": user.cover_url,
        "friend_count": len(user.friends or []),
        "posts_count": len(user.posts or []),
        "comments_count": len(user.comments or []),
        "followers_count": user.followers_count or 0,
        "is_private": user.is_private,
        "joined_date": user.joined_date,
        "friends": [],
        "posts": [],
        "comments": [],
    }


@router.patch("/me/update", response_model=UserGetResponse)
def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)

    allowed_fields = {
        "name",
        "bio",
        "phone",
        "avatar_url",
        "cover_url",
        "location",
        "is_private",
    }

    for key, value in update_data.items():
        if key in allowed_fields and value is not None:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)

    # 🔥 IMPORTANT FIX: return clean dict (NOT raw SQLAlchemy object)
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "bio": user.bio,
        "phone": user.phone,
        "location": user.location,
        "avatar_url": user.avatar_url,
        "cover_url": user.cover_url,
        "friend_count": len(user.friends or []),
        "posts_count": len(user.posts or []),
        "comments_count": len(user.comments or []),
        "followers_count": user.followers_count or 0,
        "is_private": user.is_private,
        "joined_date": user.joined_date,
        "friends": [],
        "posts": [],
        "comments": [],
    }


@router.post("/me/cover")
async def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(COVER_DIR, filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user = db.query(User).filter(User.id == current_user.id).first()
    user.cover_url = f"/uploads/covers/{filename}"

    db.commit()
    db.refresh(user)

    return {"cover_url": user.cover_url}


@router.post("/me/cover")
async def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(COVER_DIR, filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user = db.query(User).filter(User.id == current_user.id).first()
    user.cover_url = f"/uploads/covers/{filename}"

    db.commit()
    db.refresh(user)

    return {"cover_url": user.cover_url}


@router.get("/{user_id}", response_model=UserGetResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(Status_code=404, detail="User not found")

    return user


@router.get("/username/{username}", response_model=UserGetResponse)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.username == username, User.is_deleted == False)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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


@router.patch("/{user_id}", response_model=UserGetResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    for field in ["name", "bio", "avatar_url", "cover_url", "location", "is_private"]:
        value = getattr(data, field, None)
        if value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.post("/{user_id}/friends/{friend_id}")
def send_friend_request(
    user_id: int,
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if user_id == friend_id:
        raise HTTPException(status_code=400, detail="You cannot add yourself")

    user = db.query(User).filter(User.id == user_id).first()
    target = db.query(User).filter(User.id == friend_id).first()

    if not user or not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target in user.friends:
        raise HTTPException(status_code=400, detail="Already friends")

    existing = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.sender_id == user_id, FriendRequest.receiver_id == friend_id
        )
        .first()
    )

    if existing:
        return {"message": "Friend request already sent"}

    reverse = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.sender_id == friend_id, FriendRequest.receiver_id == user_id
        )
        .first()
    )

    if reverse:
        raise HTTPException(status_code=400, detail="User already sent you a request")

    request = FriendRequest(sender_id=user_id, receiver_id=friend_id)
    db.add(request)
    db.commit()

    return {"message": "Friend request sent"}


@router.get("/{user_id}/friend-requests/incoming")
def incoming_requests(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    requests = (
        db.query(FriendRequest, User)
        .join(User, FriendRequest.sender_id == User.id)
        .filter(FriendRequest.receiver_id == user_id)
        .all()
    )

    return {
        "total": len(requests),
        "data": [
            {
                "request_id": r.FriendRequest.id,
                "sender_id": r.User.id,
                "sender_username": r.User.username,
                "sender_name": r.User.name,
            }
            for r in requests
        ],
    }


@router.post("/{user_id}/friend-requests/{request_id}/accept")
def accept_request(
    user_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.receiver_id != user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.id == user_id).first()
    sender = db.query(User).filter(User.id == request.sender_id).first()

    if sender not in user.friends:
        user.friends.append(sender)
    if user not in sender.friends:
        sender.friends.append(user)

    db.delete(request)
    db.commit()

    return {"message": "Friend request accepted"}


@router.delete("/{user_id}/friend-requests/{request_id}")
def delete_request(
    user_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.sender_id != user_id and request.receiver_id != user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db.delete(request)
    db.commit()

    return {"message": "Friend request removed"}


@router.get("/{user_id}/friends")
def get_friends(
    user_id: int,
    limit: int = Query(10),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    friends = user.friends[offset : offset + limit]

    return {
        "total": len(user.friends),
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": f.id,
                "username": f.username,
                "name": f.name,
                "avatar_url": f.avatar_url,
            }
            for f in friends
        ],
    }


@router.delete("/{user_id}/friends/{friend_id}")
def remove_friend(
    user_id: int,
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.id == user_id).first()
    friend = db.query(User).filter(User.id == friend_id).first()

    if not user or not friend:
        raise HTTPException(status_code=404, detail="User not found")

    if friend in user.friends:
        user.friends.remove(friend)
        friend.friends.remove(user)
        db.commit()

    return {"message": "Friend removed"}
