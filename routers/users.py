from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


try:
    from ..db import get_db
    from ..models import User, friend_table, FriendRequest
    from ..dtos import UserCreate, UserUpdate, UserGetResponse, UserOut
    from ..auth import read_current_user
except Exception as e:
    print("errored out with exception in users")
    print(e)
    from db import get_db
    from models import User, friend_table, FriendRequest
    from dtos import UserCreate, UserUpdate, UserGetResponse
    from auth import read_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserGetResponse)
def get_me(current_user: User = Depends(read_current_user)):
    return current_user


@router.get("/users/me", response_model=UserOut)
def get_me(current_user: User = Depends(read_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "friends_count": 0,
        "followers_count": 0,
        "joined_date": current_user.created_at,
    }


@router.get("/{id}", response_model=UserGetResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/username/{username}", response_model=UserGetResponse)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch("/{id}", response_model=UserGetResponse)
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
    if data.avatar_url:
        user.avatar_url = data.avatar_url
    if data.cover_url:
        user.cover_url = data.cover_url
    if data.location:
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


@router.post("/{id}/friends/{friend_id}")
def send_friend_request(
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
    target = db.query(User).filter(User.id == friend_id).first()

    if not user or not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target in user.friends:
        raise HTTPException(status_code=400, detail="Already friends")

    existing = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.sender_id == id,
            FriendRequest.receiver_id == friend_id,
        )
        .first()
    )

    if existing:
        return {"message": "Friend request already sent"}

    reverse = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.sender_id == friend_id,
            FriendRequest.receiver_id == id,
        )
        .first()
    )

    if reverse:
        raise HTTPException(status_code=400, detail="User already sent you a request")

    request = FriendRequest(sender_id=id, receiver_id=friend_id)
    db.add(request)
    db.commit()

    return {"message": "Friend request sent"}


@router.get("/{id}/friend-requests/incoming")
def incoming_requests(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    requests = (
        db.query(FriendRequest)
        .filter(FriendRequest.receiver_id == id)
        .order_by(FriendRequest.id.desc())
        .all()
    )

    data = []
    for r in requests:
        sender = db.query(User).filter(User.id == r.sender_id).first()
        data.append(
            {
                "request_id": r.id,
                "sender_id": r.sender_id,
                "sender_username": sender.username if sender else "",
            }
        )

    return {"total": len(data), "data": data}


@router.post("/{id}/friend-requests/{request_id}/accept")
def accept_request(
    id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.receiver_id != id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.id == id).first()
    sender = db.query(User).filter(User.id == request.sender_id).first()

    if sender not in user.friends:
        user.friends.append(sender)
    if user not in sender.friends:
        sender.friends.append(user)

    db.delete(request)
    db.commit()

    return {"message": "Friend request accepted"}


@router.delete("/{id}/friend-requests/{request_id}")
def delete_request(
    id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.sender_id != id and request.receiver_id != id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db.delete(request)
    db.commit()

    return {"message": "Friend request removed"}


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
