import React from 'react';

interface LoadingProps {
  text?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Loading: React.FC<LoadingProps> = ({
  text = 'Loading...',
  size = 'md',
}) => {
  const sizeStyles = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8" role="status" aria-live="polite">
      <div
        className={`${sizeStyles[size]} animate-spin rounded-full border-4 border-gray-200 border-t-primary-600`}
        aria-hidden="true"
      />
      {text && <p className="mt-4 text-gray-600">{text}</p>}
      {!text && <span className="sr-only">Loading...</span>}
    </div>
  );
};

export const LoadingOverlay: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8">
        <Loading />
      </div>
    </div>
  );
};
