from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Post, Comment, User
from ..auth import read_current_user

router = APIRouter(tags=["Likes"])

# TODO: Create GET /posts/{post_id}/likes for list of users that liked a post


@router.get("/posts/{post_id}/likes")
def get_post_likes(
    post_id: int,
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    return {
        "count": len(post.likes),
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            }
            for user in post.likes
        ],
    }


@router.post("/posts/{post_id}/likes")
def like_post(
    post_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if current_user not in post.likes:
        post.likes.append(current_user)
        post.likes_count += 1
        db.commit()
    return {"message": "Post liked"}


@router.delete("/posts/{post_id}/likes")
def unlike_post(
    post_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if current_user in post.likes:
        post.likes.remove(current_user)
        db.commit()
    return {"message": "Post unliked"}


@router.post("/comments/{comment_id}/likes")
def like_comment(
    comment_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if current_user not in comment.likes:
        comment.likes.append(current_user)
        db.commit()
    return {"message": "Comment liked"}


@router.delete("/comments/{comment_id}/likes")
def unlike_comment(
    comment_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if current_user in comment.likes:
        comment.likes.remove(current_user)
        db.commit()
    return {"message": "Comment unliked"}
