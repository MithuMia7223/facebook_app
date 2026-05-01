from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from ..db import get_db
    from ..models import Post, Comment, User
    from ..auth import read_current_user
except ImportError:
    from db import get_db
    from models import Post, Comment, User
    from auth import read_current_user

router = APIRouter(tags=["Likes"])


# TODO: Create GET /posts/{post_id}/likes for list of users that liked a post
def create_notification(db, user_id: int, message: str):
    from ..models import Notification

    notif = Notification(user_id=user_id, message=message)
    db.add(notif)
    db.commit()


@router.get("/posts/{post_id}/likes")
def get_post_likes(
    post_id: int,
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "count": len(post.likes),
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "username": user.username,
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
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if current_user in post.likes:
        return {"message": "Already liked"}
    post.likes.append(current_user)
    post.likes_count += 1
    
    db.commit()
    return{"message": "Liked"}



@router.delete("/posts/{post_id}/likes")
def unlike_post(
    post_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if current_user in post.likes:
        post.likes.remove(current_user)
        post.likes_count = max(0, post.likes_count - 1)

        db.commit()
    return {"message": "unliked"}

@router.post("posts/{post_id}/reaction")
def react_post(
    post_id: int,
    data: dict,
    current_user: User=Depends(read_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException (status_code=404, detail="Post not found")
    reaction_type = data.get("type")

    if reaction_type =="love":
        post.love_reaction += 1
    elif reaction_type =="haha":
        post.haha_reaction += 1
    elif reaction_type =="wow":
        post.wow_reaction +1
    else:
        raise HTTPException(400, "Invalid reaction type")
    
    db.commit()

    return {"message": f"{reaction_type}added"}


@router.post("/comments/{comment_id}/likes")
def like_comment(
    comment_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if current_user not in comment.likes:
        comment.likes.append(current_user)
        comment.likes_count += 1
        db.commit()
    return {"message": "Comment liked"}


@router.delete("/comments/{comment_id}/likes")
def unlike_comment(
    comment_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if current_user in comment.likes:
        comment.likes.remove(current_user)
        comment.likes_count = max(0, comment.likes_count - 1)
        
        db.commit()
    return {"message": "Comment unliked"}