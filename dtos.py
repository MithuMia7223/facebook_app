from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    bio: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    is_private: Optional[bool] = None


class UserGetResponse(BaseModel):
    id: int
    username: str
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None

    friend_count: int
    posts_count: int
    comments_count: int
    followers_count: int

    is_private: bool
    joined_date: datetime

    friends: List[dict] = Field(default_factory=list)
    posts: List[dict] = Field(default_factory=list)
    comments: List[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    friend_count: Optional[int] = None
    followers_count: Optional[int] = None
    joined_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None


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

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    id: int
    content: str
    image_url: Optional[str]

    likes_count: int

    like_reaction: int
    love_reaction: int
    haha_reaction: int
    wow_reaction: int

    is_edited: bool

    created_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class commentResponse(BaseModel):

    id: int
    content: str
    author_id: int
    post_id: int
    likes_count: int

    class Config:
        from_attributes = True
