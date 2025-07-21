import type {
  Post,
  PostCreate,
  PostUpdate,
  Comment,
  CommentCreate,
  CommentUpdate,
  Like,
  LikeCreate,
  ApiError,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const handleResponse = async <T>(res: Response): Promise<T> => {
  if (!res.ok) {
    let error: ApiError = { code: res.status, message: res.statusText };
    try {
      error = await res.json();
    } catch (e) {
      // ignore JSON parse error, use default error
    }
    throw error;
  }
  return res.json();
};

// Posts
export const getPosts = async (): Promise<Post[]> => {
  const res = await fetch(`${BASE_URL}/posts`);
  return handleResponse<Post[]>(res);
};

export const getPost = async (postId: string): Promise<Post> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}`);
  return handleResponse<Post>(res);
};

export const createPost = async (data: PostCreate): Promise<Post> => {
  const res = await fetch(`${BASE_URL}/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Post>(res);
};

export const updatePost = async (postId: string, data: PostUpdate): Promise<Post> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Post>(res);
};

export const deletePost = async (postId: string): Promise<void> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw await res.json();
};

// Comments
export const getComments = async (postId: string): Promise<Comment[]> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}/comments`);
  return handleResponse<Comment[]>(res);
};

export const getComment = async (postId: string, commentId: string): Promise<Comment> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}/comments/${commentId}`);
  return handleResponse<Comment>(res);
};

export const createComment = async (postId: string, data: CommentCreate): Promise<Comment> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Comment>(res);
};

export const updateComment = async (
  postId: string,
  commentId: string,
  data: CommentUpdate
): Promise<Comment> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}/comments/${commentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Comment>(res);
};

export const deleteComment = async (postId: string, commentId: string): Promise<void> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}/comments/${commentId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw await res.json();
};

// Likes
export const likePost = async (postId: string, data: LikeCreate): Promise<Like> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}/likes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Like>(res);
};

export const unlikePost = async (postId: string): Promise<void> => {
  const res = await fetch(`${BASE_URL}/posts/${postId}/likes`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw await res.json();
};
