# FastAPI SNS API implementation matching openapi.yaml
import os
import yaml
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'sns_api.db')
OPENAPI_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'openapi.yaml')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Posts table
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        createdAt TEXT NOT NULL,
        updatedAt TEXT NOT NULL
    )''')
    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        postId TEXT NOT NULL,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        createdAt TEXT NOT NULL,
        updatedAt TEXT NOT NULL,
        FOREIGN KEY(postId) REFERENCES posts(id) ON DELETE CASCADE
    )''')
    # Likes table
    c.execute('''CREATE TABLE IF NOT EXISTS likes (
        postId TEXT NOT NULL,
        username TEXT NOT NULL,
        PRIMARY KEY(postId, username),
        FOREIGN KEY(postId) REFERENCES posts(id) ON DELETE CASCADE
    )''')
    conn.commit()
    conn.close()

app = FastAPI(docs_url="/docs", redoc_url=None, openapi_url=None)

# Enable CORS from everywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# --- Pydantic Models (matching openapi.yaml) ---
class Error(BaseModel):
    message: str
    code: int

class Comment(BaseModel):
    id: str
    postId: str
    username: str
    content: str
    createdAt: str
    updatedAt: str

class CommentCreateRequest(BaseModel):
    username: str
    content: str

class CommentUpdateRequest(BaseModel):
    username: str
    content: str

class Post(BaseModel):
    id: str
    username: str
    content: str
    createdAt: str
    updatedAt: str
    comments: List[Comment] = []
    likes: int

class PostCreateRequest(BaseModel):
    username: str
    content: str

class PostUpdateRequest(BaseModel):
    username: str
    content: str

class LikeRequest(BaseModel):
    username: str

# --- Utility Functions ---
import uuid
def now_iso() -> str:
    return datetime.utcnow().isoformat() + 'Z'

def get_post_by_id(conn, post_id: str):
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    return post

def get_comments_by_post(conn, post_id: str):
    rows = conn.execute("SELECT * FROM comments WHERE postId = ? ORDER BY createdAt ASC", (post_id,)).fetchall()
    return [dict(row) for row in rows]

def get_likes_count(conn, post_id: str) -> int:
    row = conn.execute("SELECT COUNT(*) as cnt FROM likes WHERE postId = ?", (post_id,)).fetchone()
    return row["cnt"] if row else 0

def get_comment_by_id(conn, post_id: str, comment_id: str):
    comment = conn.execute("SELECT * FROM comments WHERE id = ? AND postId = ?", (comment_id, post_id)).fetchone()
    return comment

# --- API Endpoints ---
# /posts GET
@app.get("/posts", response_model=List[Post], responses={500: {"model": Error}})
def list_posts(db=Depends(get_db)):
    try:
        posts = db.execute("SELECT * FROM posts ORDER BY createdAt DESC").fetchall()
        result = []
        for post in posts:
            post_id = post["id"]
            comments = [Comment(**c) for c in get_comments_by_post(db, post_id)]
            likes = get_likes_count(db, post_id)
            result.append(Post(
                id=post["id"],
                username=post["username"],
                content=post["content"],
                createdAt=post["createdAt"],
                updatedAt=post["updatedAt"],
                comments=comments,
                likes=likes
            ))
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts POST
@app.post("/posts", response_model=Post, status_code=201, responses={400: {"model": Error}, 500: {"model": Error}})
def create_post(body: PostCreateRequest, db=Depends(get_db)):
    if not body.username or not body.content:
        return JSONResponse(status_code=400, content=Error(message="username and content required", code=400).dict())
    post_id = str(uuid.uuid4())
    now = now_iso()
    try:
        db.execute("INSERT INTO posts (id, username, content, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
                   (post_id, body.username, body.content, now, now))
        db.commit()
        return Post(
            id=post_id,
            username=body.username,
            content=body.content,
            createdAt=now,
            updatedAt=now,
            comments=[],
            likes=0
        )
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId} GET
@app.get("/posts/{postId}", response_model=Post, responses={404: {"model": Error}, 500: {"model": Error}})
def get_post(postId: str, db=Depends(get_db)):
    post = get_post_by_id(db, postId)
    if not post:
        return JSONResponse(status_code=404, content=Error(message="Post not found", code=404).dict())
    comments = [Comment(**c) for c in get_comments_by_post(db, postId)]
    likes = get_likes_count(db, postId)
    return Post(
        id=post["id"],
        username=post["username"],
        content=post["content"],
        createdAt=post["createdAt"],
        updatedAt=post["updatedAt"],
        comments=comments,
        likes=likes
    )

# /posts/{postId} PATCH
@app.patch("/posts/{postId}", response_model=Post, responses={400: {"model": Error}, 404: {"model": Error}, 500: {"model": Error}})
def update_post(postId: str, body: PostUpdateRequest, db=Depends(get_db)):
    post = get_post_by_id(db, postId)
    if not post:
        return JSONResponse(status_code=404, content=Error(message="Post not found", code=404).dict())
    if not body.username or not body.content:
        return JSONResponse(status_code=400, content=Error(message="username and content required", code=400).dict())
    now = now_iso()
    try:
        db.execute("UPDATE posts SET username = ?, content = ?, updatedAt = ? WHERE id = ?",
                   (body.username, body.content, now, postId))
        db.commit()
        comments = [Comment(**c) for c in get_comments_by_post(db, postId)]
        likes = get_likes_count(db, postId)
        return Post(
            id=postId,
            username=body.username,
            content=body.content,
            createdAt=post["createdAt"],
            updatedAt=now,
            comments=comments,
            likes=likes
        )
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId} DELETE
@app.delete("/posts/{postId}", status_code=204, responses={404: {"model": Error}, 500: {"model": Error}})
def delete_post(postId: str, db=Depends(get_db)):
    post = get_post_by_id(db, postId)
    if not post:
        return JSONResponse(status_code=404, content=Error(message="Post not found", code=404).dict())
    try:
        db.execute("DELETE FROM posts WHERE id = ?", (postId,))
        db.commit()
        return Response(status_code=204)
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId}/comments GET
@app.get("/posts/{postId}/comments", response_model=List[Comment], responses={404: {"model": Error}, 500: {"model": Error}})
def list_comments(postId: str, db=Depends(get_db)):
    post = get_post_by_id(db, postId)
    if not post:
        return JSONResponse(status_code=404, content=Error(message="Post not found", code=404).dict())
    try:
        comments = [Comment(**c) for c in get_comments_by_post(db, postId)]
        return comments
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId}/comments POST
@app.post("/posts/{postId}/comments", response_model=Comment, status_code=201, responses={400: {"model": Error}, 404: {"model": Error}, 500: {"model": Error}})
def create_comment(postId: str, body: CommentCreateRequest, db=Depends(get_db)):
    post = get_post_by_id(db, postId)
    if not post:
        return JSONResponse(status_code=404, content=Error(message="Post not found", code=404).dict())
    if not body.username or not body.content:
        return JSONResponse(status_code=400, content=Error(message="username and content required", code=400).dict())
    comment_id = str(uuid.uuid4())
    now = now_iso()
    try:
        db.execute("INSERT INTO comments (id, postId, username, content, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)",
                   (comment_id, postId, body.username, body.content, now, now))
        db.commit()
        return Comment(
            id=comment_id,
            postId=postId,
            username=body.username,
            content=body.content,
            createdAt=now,
            updatedAt=now
        )
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId}/comments/{commentId} GET
@app.get("/posts/{postId}/comments/{commentId}", response_model=Comment, responses={404: {"model": Error}, 500: {"model": Error}})
def get_comment(postId: str, commentId: str, db=Depends(get_db)):
    comment = get_comment_by_id(db, postId, commentId)
    if not comment:
        return JSONResponse(status_code=404, content=Error(message="Comment not found", code=404).dict())
    return Comment(**comment)

# /posts/{postId}/comments/{commentId} PATCH
@app.patch("/posts/{postId}/comments/{commentId}", response_model=Comment, responses={400: {"model": Error}, 404: {"model": Error}, 500: {"model": Error}})
def update_comment(postId: str, commentId: str, body: CommentUpdateRequest, db=Depends(get_db)):
    comment = get_comment_by_id(db, postId, commentId)
    if not comment:
        return JSONResponse(status_code=404, content=Error(message="Comment not found", code=404).dict())
    if not body.username or not body.content:
        return JSONResponse(status_code=400, content=Error(message="username and content required", code=400).dict())
    now = now_iso()
    try:
        db.execute("UPDATE comments SET username = ?, content = ?, updatedAt = ? WHERE id = ? AND postId = ?",
                   (body.username, body.content, now, commentId, postId))
        db.commit()
        return Comment(
            id=commentId,
            postId=postId,
            username=body.username,
            content=body.content,
            createdAt=comment["createdAt"],
            updatedAt=now
        )
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId}/comments/{commentId} DELETE
@app.delete("/posts/{postId}/comments/{commentId}", status_code=204, responses={404: {"model": Error}, 500: {"model": Error}})
def delete_comment(postId: str, commentId: str, db=Depends(get_db)):
    comment = get_comment_by_id(db, postId, commentId)
    if not comment:
        return JSONResponse(status_code=404, content=Error(message="Comment not found", code=404).dict())
    try:
        db.execute("DELETE FROM comments WHERE id = ? AND postId = ?", (commentId, postId))
        db.commit()
        return Response(status_code=204)
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId}/likes POST
@app.post("/posts/{postId}/likes", status_code=201, responses={400: {"model": Error}, 404: {"model": Error}, 500: {"model": Error}})
def like_post(postId: str, body: LikeRequest, db=Depends(get_db)):
    post = get_post_by_id(db, postId)
    if not post:
        return JSONResponse(status_code=404, content=Error(message="Post not found", code=404).dict())
    if not body.username:
        return JSONResponse(status_code=400, content=Error(message="username required", code=400).dict())
    try:
        db.execute("INSERT OR IGNORE INTO likes (postId, username) VALUES (?, ?)", (postId, body.username))
        db.commit()
        return Response(status_code=201)
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# /posts/{postId}/likes DELETE
@app.delete("/posts/{postId}/likes", status_code=204, responses={404: {"model": Error}, 500: {"model": Error}})
def unlike_post(postId: str, body: LikeRequest, db=Depends(get_db)):
    post = get_post_by_id(db, postId)
    if not post:
        return JSONResponse(status_code=404, content=Error(message="Post not found", code=404).dict())
    if not body.username:
        return JSONResponse(status_code=400, content=Error(message="username required", code=400).dict())
    try:
        db.execute("DELETE FROM likes WHERE postId = ? AND username = ?", (postId, body.username))
        db.commit()
        return Response(status_code=204)
    except Exception as e:
        return JSONResponse(status_code=500, content=Error(message="Internal server error", code=500).dict())

# Serve openapi.yaml at /openapi.yaml
@app.get("/openapi.yaml", include_in_schema=False)
def serve_openapi_yaml():
    return FileResponse(OPENAPI_PATH, media_type="text/yaml")

# Serve Swagger UI at /docs (default)
# FastAPI does this by default at /docs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
