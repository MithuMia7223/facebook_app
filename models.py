from sqlalchemy import Column, Integer, String, Table, Text, ForeignKey
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
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    posts = relationship("Post", back_populates="author")
    # posts_count
    comments = relationship("Comment", back_populates="author")
    post_count = Column(Integer, insert_default=0)
    comment_count = Column(Integer, insert_default=0)

    friends = relationship(
        "User",
        secondary=friend_table,
        primaryjoin=id == friend_table.c.user_id,
        secondaryjoin=id == friend_table.c.friend_id,
        backref="friend_of",
    )
    # store friends count

    likes_posts = relationship("Post", secondary=post_likes, back_populates="likes")
    likes_comments = relationship(
        "Comment", secondary=comment_likes, back_populates="likes"
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)

    likes_count = Column(Integer, default=0)
    comment_count = Column(Integer, insert_default=0)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="post")
    likes = relationship("User", secondary=post_likes, back_populates="likes_posts")
    # likes_count
    # comments_count


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)

    likes_count = Column(Integer, default=0)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

    likes = relationship(
        "User", secondary=comment_likes, back_populates="likes_comments"
    )
    # likes_count


Base.metadata.create_all(bind=engine)
