import React from 'react';

export const PageLoadingFallback: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50" role="status" aria-live="polite">
      <div className="flex flex-col items-center space-y-4">
        <div className="relative w-16 h-16" aria-hidden="true">
          <div className="absolute top-0 left-0 w-full h-full border-4 border-primary-200 rounded-full"></div>
          <div className="absolute top-0 left-0 w-full h-full border-4 border-primary-600 rounded-full border-t-transparent animate-spin"></div>
        </div>
        <p className="text-sm text-gray-600">Loading...</p>
      </div>
    </div>
  );
};

export const ComponentLoadingFallback: React.FC = () => {
  return (
    <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
      <div className="flex items-center space-x-2">
        <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" aria-hidden="true"></div>
        <span className="text-sm text-gray-600">Loading...</span>
      </div>
    </div>
  );
};

export default PageLoadingFallback;
