import React from 'react';
import { Link } from 'react-router-dom';
import { HomeIcon, ArrowLeftIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { Button } from '../components/common/Button';

export const NotFound: React.FC = () => {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-surface-50 via-white to-primary-50 p-6">
      <div className="text-center max-w-md">
        {/* Animated 404 */}
        <div className="relative mb-8">
          <div className="text-[180px] font-black text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-accent-500 leading-none select-none">
            404
          </div>
          <div className="absolute inset-0 text-[180px] font-black text-primary-100 leading-none -z-10 blur-xl select-none">
            404
          </div>
        </div>

        {/* Content */}
        <div className="space-y-4 mb-8">
          <h1 className="text-3xl font-bold text-surface-900">
            Page not found
          </h1>
          <p className="text-lg text-surface-500 leading-relaxed">
            Sorry, we couldn't find the page you're looking for. The page might have been moved or deleted.
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link to="/">
            <Button
              variant="primary"
              size="lg"
              leftIcon={<HomeIcon className="w-5 h-5" />}
            >
              Go to Dashboard
            </Button>
          </Link>
          <Button
            variant="secondary"
            size="lg"
            leftIcon={<ArrowLeftIcon className="w-5 h-5" />}
            onClick={() => window.history.back()}
          >
            Go back
          </Button>
        </div>

        {/* Help text */}
        <p className="mt-8 text-sm text-surface-400">
          Need help?{' '}
          <a href="#" className="text-primary-600 hover:text-primary-700 font-medium">
            Contact support
          </a>
        </p>
      </div>
    </main>
  );
};

export default NotFound;
