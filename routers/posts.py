from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from fastapi.encoders import jsonable_encoder

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
    new_post = Post(content=post.content, author_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    await manager.broadcast(
        json.dumps({"event": "post:new", "data": jsonable_encoder(new_post)})
    )
    return new_post


@router.get("/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


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
    db.commit()
    db.refresh(post)
    return post


@router.get("/")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return posts


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
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}
