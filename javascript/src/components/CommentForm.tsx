import React, { useState } from "react";
import { createComment } from "../api/client";
import type { CommentCreate, ApiError } from "../api/types";

type CommentFormProps = {
  postId: string;
  onCommentAdded?: () => void;
};

const CommentForm: React.FC<CommentFormProps> = ({ postId, onCommentAdded }) => {
  const [username, setUsername] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !content.trim()) {
      setError("Username and content are required.");
      return;
    }
    setLoading(true);
    try {
      const data: CommentCreate = { username, content };
      await createComment(postId, data);
      setUsername("");
      setContent("");
      if (onCommentAdded) onCommentAdded();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message || "Failed to add comment");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="bg-gray-50 rounded-lg p-2 flex flex-col gap-2" aria-label="Comment Form" onSubmit={handleSubmit}>
      <input
        className="border rounded px-2 py-1"
        type="text"
        placeholder="Your name"
        value={username}
        onChange={e => setUsername(e.target.value)}
        aria-label="Username"
        required
      />
      <textarea
        className="border rounded px-2 py-1"
        placeholder="Add a comment..."
        value={content}
        onChange={e => setContent(e.target.value)}
        aria-label="Comment content"
        required
        rows={2}
      />
      <button
        type="submit"
        className="bg-blue-600 text-white rounded px-3 py-1 disabled:opacity-50"
        disabled={loading}
        aria-label="Submit comment"
      >
        {loading ? "Posting..." : "Post Comment"}
      </button>
      {error && <div className="text-red-500 text-xs">{error}</div>}
    </form>
  );
};

export default CommentForm;
