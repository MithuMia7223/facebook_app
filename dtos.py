from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    bio: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None


class PostCreate(BaseModel):
    content: str


class PostUpdate(BaseModel):
    content: Optional[str] = None


class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class UserGetMeResponse(BaseModel):
    id: int
    username: str
    name: str
    bio: str
