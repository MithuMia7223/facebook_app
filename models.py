from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Table,
    Text,
    ForeignKey,
    UniqueConstraint,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import relationship

try:
    from .db import Base, engine
except ImportError:
    from db import Base, engine


friend_table = Table(
    "friends",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("friend_id", Integer, ForeignKey("users.id"), primary_key=True),
)

post_likes = Table(
    "post_likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
)

comment_likes = Table(
    "comment_likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("comment_id", Integer, ForeignKey("comments.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    joined_date = Column(DateTime, default=datetime.utcnow)

    post_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    friend_count = Column(Integer, default=0)
    followers_count = Column(Integer, default=0)

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    friends = relationship(
        "User",
        secondary=friend_table,
        primaryjoin=id == friend_table.c.user_id,
        secondaryjoin=id == friend_table.c.friend_id,
        backref="friend_of",
    )

    likes_posts = relationship("Post", secondary=post_likes, back_populates="likes")
    likes_comments = relationship(
        "Comment", secondary=comment_likes, back_populates="likes"
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)

    image_url = Column(String, nullable=True)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")

    like_reaction = Column(Integer, default=0)
    love_reaction = Column(Integer, default=0)
    haha_reaction = Column(Integer, default=0)
    wow_reaction = Column(Integer, default=0)

    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

    likes_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")

    created_at = Column(DateTime, default=datetime.utcnow)

    comments = relationship("Comment", back_populates="post")
    likes = relationship("User", secondary=post_likes, back_populates="likes_posts")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)

    likes_count = Column(Integer, default=0)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable= True)


    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

    created_at = Column(DateTime, default=datetime.utcnow)
    post = relationship("Post")
    author = relationship("User")


    likes = relationship(
        "User", secondary=comment_likes, back_populates="likes_comments"
    )
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)

    is_read = Column(Boolean, default=datetime.utcnow)
    


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True)

    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sender_id", "receiver_id", name="uq_sender_receiver"),
    )


Base.metadata.create_all(bind=engine)
