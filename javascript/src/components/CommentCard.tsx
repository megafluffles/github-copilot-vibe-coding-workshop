import React from "react";
import type { Comment } from "../api/types";

type CommentCardProps = {
  comment: Comment;
};

const CommentCard: React.FC<CommentCardProps> = ({ comment }) => {
  return (
    <div className="bg-gray-100 rounded p-2" tabIndex={0} aria-label="Comment">
      <div className="flex items-center gap-2">
        <span className="font-semibold">{comment.username}</span>
        <span className="text-xs text-gray-400">{new Date(comment.createdAt).toLocaleString()}</span>
      </div>
      <div className="text-gray-800 text-sm">{comment.content}</div>
    </div>
  );
};

export default CommentCard;
