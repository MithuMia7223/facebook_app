from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from ..db import get_db
    from ..models import Notification, User
    from ..auth import read_current_user
except ImportError:
    from db import get_db
    from models import Notification, User
    from auth import read_current_user


router = APIRouter(prefix="/notifications", tags=["Notifications"])



@router.get("/")
def get_notifications(
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.id.desc())
        .all()
    )

    return {
        "total": len(notifications),
        "data": [
            {
                "id": n.id,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in notifications
        ],
    }


@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(read_current_user),
    db: Session = Depends(get_db),
):

    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}

