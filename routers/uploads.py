from fastapi import APIRotuer, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os 
import uuid
import shutil

from ..db import get_db
from ..models import User 
from ..auth import read_current_user

router = APIRotuer(prefix="/users", tags=["Users"])

UPLOD_DIR = "uploads/avatars"
os.makedirs(UPLOD_DIR, exist_ok=True)

@router.get("/me")
def get_me(current_user: User=Depends(read_current_user)):

    return{
        "id": current_user.id,
        "username":current_user.username,
        "name": current_user.name,
        "bio": current_user.bio,
        "avatar_url": current_user.avatar_url
    }

@router.post("/me/avatar")

async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User=Depends(read_current_user),
    db: Session = Depends(get_db),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.avatar_url = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    
    return{
        "message": "Avatar upload successfully",
        "avatar_url": current_user.avatar_url
    }