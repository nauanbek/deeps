import { renderHook } from '@testing-library/react';
import { useAuth } from '../useAuth';

// Mock the AuthContext to return undefined (simulating usage outside provider)
jest.mock('../../contexts/AuthContext', () => ({
  __esModule: true,
  default: {
    Consumer: ({ children }: { children: (value: undefined) => React.ReactNode }) => children(undefined),
  },
}));

describe('useAuth Hook', () => {
  it('should throw error when used outside AuthProvider', () => {
    // Suppress console.error for this test
    const originalError = console.error;
    console.error = jest.fn();

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');

    console.error = originalError;
  });
});
