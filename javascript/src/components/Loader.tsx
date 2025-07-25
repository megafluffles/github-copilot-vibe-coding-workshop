import React from "react";

const Loader: React.FC = () => (
  <div className="flex justify-center items-center py-8" aria-label="Loading">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

export default Loader;
