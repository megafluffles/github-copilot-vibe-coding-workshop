import React, { useState } from "react";
import type { Post } from "../api/types";
import LikeButton from "./LikeButton";
import CommentList from "./CommentList";
import CommentForm from "./CommentForm";
import { likePost, unlikePost } from "../api/client";

type PostCardProps = {
  post: Post;
};

const PostCard: React.FC<PostCardProps> = ({ post }) => {
  // For demo, assume username is 'demo-user'. In real app, get from auth/user context.
  const username = "demo-user";
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(post.likes);
  const [likeError, setLikeError] = useState<string | null>(null);
  const [commentsKey, setCommentsKey] = useState(0); // for refreshing CommentList
  const handleLike = async () => {
    setLikeError(null);
    if (!liked) {
      setLiked(true);
      setLikeCount((c) => c + 1);
      try {
        await likePost(post.id, { username });
      } catch (err) {
        setLiked(false);
        setLikeCount((c) => c - 1);
        setLikeError("Failed to like post");
      }
    } else {
      setLiked(false);
      setLikeCount((c) => c - 1);
      try {
        await unlikePost(post.id);
      } catch (err) {
        setLiked(true);
        setLikeCount((c) => c + 1);
        setLikeError("Failed to unlike post");
      }
    }
  };
  return (
    <article className="bg-white rounded-lg shadow p-4 flex flex-col gap-2" tabIndex={0} aria-label="Post">
      <div className="flex items-center gap-2">
        <span className="font-semibold">{post.username}</span>
        <span className="text-xs text-gray-400">{new Date(post.createdAt).toLocaleString()}</span>
      </div>
      <div className="text-base text-gray-800">{post.content}</div>
      <div className="flex items-center gap-4 mt-2">
        <span className="text-sm text-gray-500">{likeCount} Likes</span>
        <span className="text-sm text-gray-500">{post.comments.length} Comments</span>
        <LikeButton liked={liked} onClick={handleLike} />
      </div>
      {likeError && <div className="text-red-500 text-xs mt-1">{likeError}</div>}
      <div className="mt-4">
        <h3 className="font-semibold text-sm mb-1">Comments</h3>
        <CommentForm postId={post.id} onCommentAdded={() => setCommentsKey(k => k + 1)} />
        <CommentList key={commentsKey} postId={post.id} />
      </div>
    </article>
  );
};

export default PostCard;
