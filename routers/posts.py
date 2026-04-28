from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import json
from fastapi.encoders import jsonable_encoder
from datetime import datetime

try:
    from ..db import get_db
    from ..models import Post, User
    from ..dtos import PostCreate, PostUpdate
    from ..auth import read_current_user
    from .socket import manager
except ImportError:
    from db import get_db
    from models import Post, User
    from dtos import PostCreate, PostUpdate
    from auth import read_current_user
    from socket import manager

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/")
async def create_post(
    post: PostCreate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    new_post = Post(
        content=post.content,
        image_url=post.image_url,
        author_id=current_user.id,
        created_at=datetime.utcnow(),
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    await manager.broadcast(
        json.dumps({"event": "post:new", "data": jsonable_encoder(new_post)})
    )
    return new_post


@router.get("/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id, Post.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "id": post.id,
        "content": post.content,
        "image_url": post.image_url,
        "author_name": post.author.name if post.author else None,
        "likes_count": post.likes.count,
        "love_count": post.love_count,
        "haha_count": post.haha.count,
        "wow_count": post.wow_count,
        "comment_count": post.comment_count,
        "is_edited": post.is_edited,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


@router.get("/feed")
def get_feed(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(read_current_user),
):

    friend_ids = [f.id for f in user.friends]

    posts = (
        db.query(Post)
        .filter(
            Post.is_deleted == False,
            (Post.author_id.in_(friend_ids)) | (Post.author_id == user.id),
        )
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return posts


@router.patch("/{id}")
def update_post(
    id: int,
    data: PostUpdate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if data.content:
        post.content = data.content

    if data.image_url:
        post.image_url = data.image_url

    db.commit()
    db.refresh(post)
    return post


@router.get("/")
def get_posts(
    limit: int = Query(10),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    posts = (
        db.query(Post)
        .filter(Post.is_deleted == False)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return posts


@router.delete("/search")
def search_posts(
    q: str,
    db: Session = Depends(get_db),
):
    return (
        db.query(Post).filter(Post.content.contains(q), Post.is_deleted == False).all()
    )


@router.get("/{id}/like")
def toggle_like(
    id: int,
    db: Session = Depends(get_db),
    user: User = Depends(read_current_user),
):
    post = db.query(Post).filter(Post.id == id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if user in post.likes:
        post.likes.remove(user)
        post.likes_count -= 1
    else:
        post.likes.remove(user)
        post.likes_count += 1

    db.commit()
    return {"message": "ok"}


@router.post("/{id}/reaction")
def react(
    id: int,
    type: str,
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if type == "love":
        post.love_count += 1
    elif type == "haha":
        post.haha_count += 1
    elif type == "wow":
        post.wow_count += 1

    db.commit()

    return {"message": "reaction added"}


@router.delete("/{id}")
def delete_post(
    id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    post.is_deleted = True

    db.commit()

    return {"message": "Post deleted"}
