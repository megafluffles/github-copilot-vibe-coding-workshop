import React, { useState } from "react";
import { createPost } from "../api/client";
import type { PostCreate, ApiError } from "../api/types";

type PostFormProps = {
  onPostCreated?: () => void;
};

const PostForm: React.FC<PostFormProps> = ({ onPostCreated }) => {
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
      const data: PostCreate = { username, content };
      await createPost(data);
      setUsername("");
      setContent("");
      if (onPostCreated) onPostCreated();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message || "Failed to create post");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="bg-gray-50 rounded-lg p-4 flex flex-col gap-2" aria-label="Post Form" onSubmit={handleSubmit}>
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
        placeholder="What's on your mind?"
        value={content}
        onChange={e => setContent(e.target.value)}
        aria-label="Post content"
        required
        rows={3}
      />
      <button
        type="submit"
        className="bg-blue-600 text-white rounded px-3 py-1 disabled:opacity-50"
        disabled={loading}
        aria-label="Submit post"
      >
        {loading ? "Posting..." : "Post"}
      </button>
      {error && <div className="text-red-500 text-xs">{error}</div>}
    </form>
  );
};

export default PostForm;
