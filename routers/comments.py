from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Comment, User
from ..dtos import CommentCreate, CommentUpdate
from ..auth import read_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/posts/{post_id}")
def create_comment(
    post_id: int,
    comment: CommentCreate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    new_comment = Comment(
        content=comment.content, author_id=current_user.id, post_id=post_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.get("/posts/{post_id}")
def get_post_comments(
    post_id: int,
    limit: int = Query(10),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(Comment).filter(Comment.post_id == post_id).count()
    return {"total": total, "limit": limit, "offset": offset, "data": comments}


@router.patch("/{id}")
def update_comment(
    id: int,
    data: CommentUpdate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == id).first()
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if data.content:
        comment.content = data.content
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{id}")
def delete_comment(
    id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == id).first()
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}
