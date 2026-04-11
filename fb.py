from fastapi import FastAPI

try:
    from .routers import users, posts, comments, likes, socket
except ImportError:
    from routers import users, posts, comments, likes, socket


app = FastAPI(title="Facebook4 API", version="1.0.0")

app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
app.include_router(socket.router)

# git tutorial - learn with sumit