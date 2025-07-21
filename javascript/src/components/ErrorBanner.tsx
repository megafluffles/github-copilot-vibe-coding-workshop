import React from "react";

type ErrorBannerProps = {
  message: string;
};

const ErrorBanner: React.FC<ErrorBannerProps> = ({ message }) => (
  <div className="w-full bg-red-600 text-white text-center py-2" role="alert" tabIndex={0} aria-label="API Error">
    {message}
  </div>
);

export default ErrorBanner;
