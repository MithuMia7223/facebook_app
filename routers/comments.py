from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

try:
    from ..db import get_db
    from ..models import Comment, User, Post
    from ..dtos import CommentCreate, CommentUpdate
    from ..auth import read_current_user
except ImportError:
    from db import get_db
    from models import Comment, User, Post
    from dtos import CommentCreate, CommentUpdate
    from auth import read_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])

def Create_notification(db, user_id: int, message: str):
    try:
        from ..models import Notification
        notif =Notification(user_id=user_id, message=message)
        db.add(notif)
        db.commit()
    except:
        pass




@router.post("/posts/{post_id}")
def create_comment(
    post_id: int,
    comment: CommentCreate,
    parent_id: int = None,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = Comment(
        content=comment.content, author_id=current_user.id, post_id=post_id, parent_id=parent_id
    )
    post.comment_count += 1

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    if post.author_id != current_user.id:
        Create_notification(
            db,
            post.author_id,
            "Someone commented on your post"
        )

    return new_comment


@router.get("/posts/{post_id}")
def get_post_comments(
    post_id: int,
    limit: int = Query(10),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.parent_id == None )
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return {
        "total": len(comments),
        "data": comments
    }
def get_replies(comment_id: int, db):
    return db.query(Comment).filter(Comment.parent_id == comment_id).all()

@router.get("/tree/{post_id}")
def comment_tree(post_id: int, db: Session = Depends(get_db)):

    comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id == None

    ).all()

    def build(comment):
        return{
            "id": comment.id,
            "content": comment.content,
            "author_id": comment.author_id,
            "replies": [
                build(reply) for reply in get_replies(comment.id, db)

            ]
        }
    
    return [build(c) for c in comments]




@router.patch("/{comment_id}")
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if data.content is not None:
        comment.content = data.content
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if post and post.comment_count > 0:
        post.comment_count -= 1
        
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}

