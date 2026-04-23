from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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


@router.get("/me", response_model=UserGetResponse)
def get_me(current_user: User = Depends(read_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "bio": current_user.bio,
        "avatar_url": current_user.avatar_url,
        "cover_url": current_user.cover_url,
        "location": current_user.location,
        "friend_count": len(current_user.friends) if current_user.friends else 0,
        "followers_count": 0,
        "is_private": current_user.is_private,
        "joined_date": current_user.created_at,
    }


@router.get("/{user_id}", response_model=UserGetResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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

    if data.name is not None:
        user.name = data.name
    if data.bio is not None:
        user.bio = data.bio
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
    if data.cover_url is not None:
        user.cover_url = data.cover_url
    if data.location is not None:
        user.location = data.location
    if data.is_private is not None:
        user.is_private = data.is_private

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
