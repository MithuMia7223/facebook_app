from fastapi import FastAPI
from .routers import users, posts, comments, likes


app = FastAPI(title="Facebook4 API", version="1.0.0")

app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)

# git tutorial - learn with sumit
