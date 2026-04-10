from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

try:
    from ..db import get_db
    from ..models import User, friend_table, FriendRequest
    from ..dtos import UserCreate, UserUpdate, UserGetMeResponse
    from ..auth import read_current_user
except ImportError:
    from db import get_db
    from models import User, friend_table, FriendRequest
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
    # Backward-compatible endpoint: now this creates a friend request.
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

    existing_same_direction = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.sender_id == id,
            FriendRequest.receiver_id == friend_id,
        )
        .first()
    )
    if existing_same_direction:
        return {"message": "Friend request already sent"}

    incoming_from_target = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.sender_id == friend_id,
            FriendRequest.receiver_id == id,
        )
        .first()
    )
    if incoming_from_target:
        raise HTTPException(
            status_code=400,
            detail="This user already sent you a request. Accept it from requests.",
        )

    request = FriendRequest(sender_id=id, receiver_id=friend_id)
    db.add(request)
    db.commit()
    return {"message": "Friend request sent"}


@router.post("/{id}/friend-requests/{target_id}")
def send_friend_request(
    id: int,
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    return add_friend(id=id, friend_id=target_id, db=db, current_user=current_user)


@router.get("/{id}/friend-requests/incoming")
def get_incoming_friend_requests(
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
    for request in requests:
        sender = db.query(User).filter(User.id == request.sender_id).first()
        data.append(
            {
                "request_id": request.id,
                "sender_id": request.sender_id,
                "sender_username": sender.username if sender else "",
            }
        )
    return {"total": len(data), "data": data}


@router.get("/{id}/friend-requests/outgoing")
def get_outgoing_friend_requests(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    requests = (
        db.query(FriendRequest)
        .filter(FriendRequest.sender_id == id)
        .order_by(FriendRequest.id.desc())
        .all()
    )
    data = []
    for request in requests:
        receiver = db.query(User).filter(User.id == request.receiver_id).first()
        data.append(
            {
                "request_id": request.id,
                "receiver_id": request.receiver_id,
                "receiver_username": receiver.username if receiver else "",
            }
        )
    return {"total": len(data), "data": data}


@router.post("/{id}/friend-requests/{request_id}/accept")
def accept_friend_request(
    id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if request.receiver_id != id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.id == id).first()
    sender = db.query(User).filter(User.id == request.sender_id).first()
    if not user or not sender:
        raise HTTPException(status_code=404, detail="User not found")

    if sender not in user.friends:
        user.friends.append(sender)
    if user not in sender.friends:
        sender.friends.append(user)

    db.delete(request)
    db.commit()
    return {"message": "Friend request accepted"}


@router.delete("/{id}/friend-requests/{request_id}")
def delete_friend_request(
    id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(read_current_user),
):
    if id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if request.receiver_id != id and request.sender_id != id:
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
