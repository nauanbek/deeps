import React from 'react';

/**
 * SkipNavigation Component
 *
 * Provides a skip link for keyboard users to bypass navigation and jump directly to main content.
 * Visually hidden by default, becomes visible when focused (e.g., via Tab key).
 *
 * WCAG 2.1 Criterion: 2.4.1 Bypass Blocks (Level A)
 */
export const SkipNavigation: React.FC = () => {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2"
    >
      Skip to main content
    </a>
  );
};

export default SkipNavigation;
