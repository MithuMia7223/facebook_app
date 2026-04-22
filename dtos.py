from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    bio: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    is_private: Optional[bool] = None


class UserGetResponse(BaseModel):
    id: int
    username: str
    name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    cover_url: Optional[str]
    location: Optional[str]
    friend_count: int
    followers_count: int
    is_private: bool
    joined_date: datetime


class UserOut(BaseModel):
    id: int
    username: str
    friend_count: Optional[int] = None
    followers_count: Optional[int] = None
    joined_count: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    content: str


class PostUpdate(BaseModel):
    content: Optional[str] = None


class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    content: str
    author_id: int
    likes_count: int
    comment_count: int


class commentResponse(BaseModel):

    id: int
    content: str
    author_id: int
    post_id: int
    likes_count: int
