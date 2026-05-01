from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

try:
    from .routers import users, posts, comments, likes, socket, uploads
except ImportError:
    from routers import users, posts, comments, likes, socket, uploads


app = FastAPI(title="Facebook4 API", version="1.0.0")

os.makedirs("uploads/avatars", exist_ok=True)
os.makedirs("uploads/covers", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
app.include_router(socket.router)
app.include_router(uploads.router)
