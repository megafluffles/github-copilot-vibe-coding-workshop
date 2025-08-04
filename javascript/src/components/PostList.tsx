import React from "react";
import type { Post } from "../api/types";
import PostCard from "./PostCard";

type PostListProps = {
  posts: Post[];
};

const PostList: React.FC<PostListProps> = ({ posts }) => {
  if (!posts.length) {
    return <div className="text-center text-gray-500">No posts yet.</div>;
  }
  return (
    <section className="w-full max-w-2xl mx-auto flex flex-col gap-4" aria-label="Posts List">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </section>
  );
};

export default PostList;
