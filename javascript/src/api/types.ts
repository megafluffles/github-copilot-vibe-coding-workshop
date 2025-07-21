// Types generated from openapi.yaml

export type Post = {
  id: string;
  username: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  comments: Comment[];
  likes: number;
};

export type PostCreate = {
  username: string;
  content: string;
};

export type PostUpdate = {
  username: string;
  content: string;
};

export type Comment = {
  id: string;
  postId: string;
  username: string;
  content: string;
  createdAt: string;
  updatedAt: string;
};

export type CommentCreate = {
  username: string;
  content: string;
};

export type CommentUpdate = {
  username: string;
  content: string;
};

export type Like = {
  postId: string;
  username: string;
  createdAt: string;
};

export type LikeCreate = {
  username: string;
};

export type ApiError = {
  code: number;
  message: string;
};
