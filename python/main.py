import json
from pathlib import Path
from fastapi import FastAPI, Request, Response, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import aiosqlite

OPENAPI_PATH = Path(__file__).parent.parent / "openapi.yaml"
DB_PATH = Path(__file__).parent / "sns_api.db"

def load_openapi_spec() -> dict:
    import yaml
    with OPENAPI_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

openapi_spec = load_openapi_spec()

app = FastAPI(
    title=openapi_spec["info"]["title"],
    description=openapi_spec["info"].get("description", ""),
    version=openapi_spec["info"]["version"],
    openapi_url=None,  # Disable default /openapi.json
    docs_url=None,     # Disable default /docs
    redoc_url=None     # Disable default /redoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL,
            likes INTEGER NOT NULL DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            postId TEXT NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            postId TEXT NOT NULL,
            username TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            PRIMARY KEY (postId, username)
        )
        """)
        await db.commit()

# Serve OpenAPI spec at default endpoint
@app.get("/openapi.yaml", response_class=Response, include_in_schema=False)
def get_openapi_yaml():
    return Response(content=OPENAPI_PATH.read_text(encoding="utf-8"), media_type="application/yaml")

# Serve Swagger UI at default endpoint
@app.get("/", include_in_schema=False)
def swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.yaml", title=app.title + " - Swagger UI")

# --- Endpoint implementations below ---
# All endpoints must match openapi.yaml exactly. Only implement those defined in openapi.yaml.
# Use Pydantic models for input validation and response schemas.

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

# --- Schemas ---
class Error(BaseModel):
    code: int
    message: str

class Post(BaseModel):
    id: str
    username: str
    content: str
    createdAt: str
    updatedAt: str
    comments: List["Comment"] = []
    likes: int

class PostCreate(BaseModel):
    username: str
    content: str

class PostUpdate(BaseModel):
    username: str
    content: str

class Comment(BaseModel):
    id: str
    postId: str
    username: str
    content: str
    createdAt: str
    updatedAt: str

class CommentCreate(BaseModel):
    username: str
    content: str

class CommentUpdate(BaseModel):
    username: str
    content: str

class Like(BaseModel):
    postId: str
    username: str
    createdAt: str

class LikeCreate(BaseModel):
    username: str

# --- Helper functions ---
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

# --- Post Endpoints ---
@app.get("/posts", response_model=List[Post])
async def list_posts():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        posts = await db.execute_fetchall("SELECT * FROM posts ORDER BY createdAt DESC")
        result = []
        for post in posts:
            comments = await db.execute_fetchall("SELECT * FROM comments WHERE postId = ? ORDER BY createdAt ASC", (post["id"],))
            result.append(Post(
                id=post["id"],
                username=post["username"],
                content=post["content"],
                createdAt=post["createdAt"],
                updatedAt=post["updatedAt"],
                comments=[Comment(**dict(c)) for c in comments],
                likes=post["likes"]
            ))
        return result

@app.post("/posts", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(body: PostCreate):
    if not body.username or not body.content:
        raise HTTPException(status_code=400, detail="username and content required")
    post_id = str(uuid.uuid4())
    now = now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO posts (id, username, content, createdAt, updatedAt, likes) VALUES (?, ?, ?, ?, ?, 0)",
            (post_id, body.username, body.content, now, now)
        )
        await db.commit()
    return Post(
        id=post_id,
        username=body.username,
        content=body.content,
        createdAt=now,
        updatedAt=now,
        comments=[],
        likes=0
    )

@app.get("/posts/{postId}", response_model=Post)
async def get_post(postId: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        comments = await db.execute_fetchall("SELECT * FROM comments WHERE postId = ? ORDER BY createdAt ASC", (postId,))
        return Post(
            id=post["id"],
            username=post["username"],
            content=post["content"],
            createdAt=post["createdAt"],
            updatedAt=post["updatedAt"],
            comments=[Comment(**dict(c)) for c in comments],
            likes=post["likes"]
        )

@app.patch("/posts/{postId}", response_model=Post)
async def update_post(postId: str, body: PostUpdate):
    if not body.username or not body.content:
        raise HTTPException(status_code=400, detail="username and content required")
    async with aiosqlite.connect(DB_PATH) as db:
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        now = now_iso()
        await db.execute(
            "UPDATE posts SET username = ?, content = ?, updatedAt = ? WHERE id = ?",
            (body.username, body.content, now, postId)
        )
        await db.commit()
        comments = await db.execute_fetchall("SELECT * FROM comments WHERE postId = ? ORDER BY createdAt ASC", (postId,))
        updated_post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        return Post(
            id=updated_post["id"],
            username=updated_post["username"],
            content=updated_post["content"],
            createdAt=updated_post["createdAt"],
            updatedAt=updated_post["updatedAt"],
            comments=[Comment(**dict(c)) for c in comments],
            likes=updated_post["likes"]
        )

@app.delete("/posts/{postId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(postId: str):
    async with aiosqlite.connect(DB_PATH) as db:
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        await db.execute("DELETE FROM posts WHERE id = ?", (postId,))
        await db.execute("DELETE FROM comments WHERE postId = ?", (postId,))
        await db.execute("DELETE FROM likes WHERE postId = ?", (postId,))
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Comment Endpoints ---
@app.get("/posts/{postId}/comments", response_model=List[Comment])
async def list_comments(postId: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        comments = await db.execute_fetchall("SELECT * FROM comments WHERE postId = ? ORDER BY createdAt ASC", (postId,))
        return [Comment(**dict(c)) for c in comments]

@app.post("/posts/{postId}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(postId: str, body: CommentCreate):
    if not body.username or not body.content:
        raise HTTPException(status_code=400, detail="username and content required")
    async with aiosqlite.connect(DB_PATH) as db:
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        comment_id = str(uuid.uuid4())
        now = now_iso()
        await db.execute(
            "INSERT INTO comments (id, postId, username, content, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)",
            (comment_id, postId, body.username, body.content, now, now)
        )
        await db.commit()
    return Comment(
        id=comment_id,
        postId=postId,
        username=body.username,
        content=body.content,
        createdAt=now,
        updatedAt=now
    )

@app.get("/posts/{postId}/comments/{commentId}", response_model=Comment)
async def get_comment(postId: str, commentId: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        comment = await db.execute_fetchone("SELECT * FROM comments WHERE id = ? AND postId = ?", (commentId, postId))
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return Comment(**dict(comment))

@app.patch("/posts/{postId}/comments/{commentId}", response_model=Comment)
async def update_comment(postId: str, commentId: str, body: CommentUpdate):
    if not body.username or not body.content:
        raise HTTPException(status_code=400, detail="username and content required")
    async with aiosqlite.connect(DB_PATH) as db:
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        comment = await db.execute_fetchone("SELECT * FROM comments WHERE id = ? AND postId = ?", (commentId, postId))
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        now = now_iso()
        await db.execute(
            "UPDATE comments SET username = ?, content = ?, updatedAt = ? WHERE id = ? AND postId = ?",
            (body.username, body.content, now, commentId, postId)
        )
        await db.commit()
        updated_comment = await db.execute_fetchone("SELECT * FROM comments WHERE id = ? AND postId = ?", (commentId, postId))
        return Comment(**dict(updated_comment))

@app.delete("/posts/{postId}/comments/{commentId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(postId: str, commentId: str):
    async with aiosqlite.connect(DB_PATH) as db:
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        comment = await db.execute_fetchone("SELECT * FROM comments WHERE id = ? AND postId = ?", (commentId, postId))
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        await db.execute("DELETE FROM comments WHERE id = ? AND postId = ?", (commentId, postId))
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Like Endpoints ---
@app.post("/posts/{postId}/likes", response_model=Like, status_code=status.HTTP_201_CREATED)
async def like_post(postId: str, body: LikeCreate):
    if not body.username:
        raise HTTPException(status_code=400, detail="username required")
    async with aiosqlite.connect(DB_PATH) as db:
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        like = await db.execute_fetchone("SELECT * FROM likes WHERE postId = ? AND username = ?", (postId, body.username))
        if like:
            raise HTTPException(status_code=400, detail="Already liked")
        now = now_iso()
        await db.execute("INSERT INTO likes (postId, username, createdAt) VALUES (?, ?, ?)", (postId, body.username, now))
        await db.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (postId,))
        await db.commit()
    return Like(postId=postId, username=body.username, createdAt=now)

@app.delete("/posts/{postId}/likes", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(postId: str, request: Request):
    data = await request.json()
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="username required")
    async with aiosqlite.connect(DB_PATH) as db:
        post = await db.execute_fetchone("SELECT * FROM posts WHERE id = ?", (postId,))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        like = await db.execute_fetchone("SELECT * FROM likes WHERE postId = ? AND username = ?", (postId, username))
        if not like:
            raise HTTPException(status_code=404, detail="Like not found")
        await db.execute("DELETE FROM likes WHERE postId = ? AND username = ?", (postId, username))
        await db.execute("UPDATE posts SET likes = likes - 1 WHERE id = ? AND likes > 0", (postId,))
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Error handler for HTTPException ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail}
    )

# --- Run the app ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
