import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';
import '../src/index.css';

// Create a QueryClient for Storybook
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: Infinity,
      cacheTime: Infinity,
    },
  },
});

// Mock AuthContext for components that use authentication
const MockAuthProvider = ({ children }) => {
  return <>{children}</>;
};

const preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: '#ffffff',
        },
        {
          name: 'dark',
          value: '#1f2937',
        },
      ],
    },
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <MockAuthProvider>
            <div className="min-h-screen bg-gray-50 p-8">
              <Story />
            </div>
          </MockAuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    ),
  ],
};

export default preview;
