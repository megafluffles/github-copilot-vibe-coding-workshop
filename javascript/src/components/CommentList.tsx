import React, { useEffect, useState } from "react";
import type { Comment, ApiError } from "../api/types";
import { getComments } from "../api/client";
import CommentCard from "./CommentCard";
import Loader from "./Loader";

type CommentListProps = {
  postId: string;
};

const CommentList: React.FC<CommentListProps> = ({ postId }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchComments = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getComments(postId);
        setComments(data);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.message || "API unavailable");
      } finally {
        setLoading(false);
      }
    };
    fetchComments();
  }, [postId]);

  if (loading) return <Loader />;
  if (error) return <div className="text-red-500 text-xs">{error}</div>;
  if (!comments.length) return <div className="text-gray-400 text-sm">No comments yet.</div>;

  return (
    <section className="flex flex-col gap-2" aria-label="Comments List">
      {comments.map((comment) => (
        <CommentCard key={comment.id} comment={comment} />
      ))}
    </section>
  );
};

export default CommentList;
