from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Post, User
from ..dtos import PostCreate, PostUpdate
from ..auth import read_current_user

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/")
def create_post(
    post: PostCreate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    print(post)
    print(current_user)
    new_post = Post(content=post.content, author_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
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
    if not posts:
        raise HTTPException(status_code=404, detail="posts not found")
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
