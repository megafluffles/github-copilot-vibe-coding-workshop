import React, { useEffect, useState } from "react";
import PostList from "./components/PostList";
import PostForm from "./components/PostForm";
import ErrorBanner from "./components/ErrorBanner";
import Loader from "./components/Loader";
import { getPosts } from "./api/client";
import type { Post, ApiError } from "./api/types";

const App: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  const fetchPosts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPosts();
      setPosts(data);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message || "API unavailable");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  return (
    <main className="min-h-screen bg-gray-100">
      {error && <ErrorBanner message={error} />}
      <div className="max-w-2xl mx-auto py-8 px-2 flex flex-col gap-6">
        <h1 className="text-3xl font-bold text-center">Simple Social Media</h1>
        <PostForm onPostCreated={fetchPosts} />
        {loading ? <Loader /> : <PostList posts={posts} />}
      </div>
    </main>
  );
};

export default App;
