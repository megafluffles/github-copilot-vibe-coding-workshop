import React from "react";

type LikeButtonProps = {
  liked: boolean;
  onClick: () => void;
};

const LikeButton: React.FC<LikeButtonProps> = ({ liked, onClick }) => {
  return (
    <button
      type="button"
      className="flex items-center gap-1 px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-pressed={liked}
      aria-label={liked ? "Unlike post" : "Like post"}
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onClick(); }}
    >
      <span className={liked ? "text-blue-600" : "text-gray-400"}>♥</span>
      <span>{liked ? "Liked" : "Like"}</span>
    </button>
  );
};

export default LikeButton;
