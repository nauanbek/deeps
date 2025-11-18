/**
 * Tests for PasswordStrengthMeter component
 */

import { render, screen, waitFor } from '@testing-library/react';
import { PasswordStrengthMeter } from './PasswordStrengthMeter';
import { apiClient } from '../../api/client';

// Mock API client
jest.mock('../../api/client');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('PasswordStrengthMeter', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing for empty password', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    expect(container.firstChild).toBeNull();
  });

  it('shows loading state while checking strength', async () => {
    // Mock delayed API response
    mockedApiClient.post.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                data: {
                  strength: 'medium',
                  score: 60,
                  suggestions: ['Use at least 12 characters'],
                },
              } as any),
            100
          )
        )
    );

    render(<PasswordStrengthMeter password="TestPass123" />);

    // Should show loading state
    expect(screen.getByText(/checking password strength/i)).toBeInTheDocument();

    // Wait for API call to complete
    await waitFor(() => {
      expect(screen.queryByText(/checking password strength/i)).not.toBeInTheDocument();
    });
  });

  it('displays very weak strength correctly', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: {
        strength: 'very_weak',
        score: 15,
        suggestions: ['Add uppercase letters', 'Add numbers'],
      },
    } as any);

    render(<PasswordStrengthMeter password="abc" />);

    await waitFor(() => {
      expect(screen.getByText('Very Weak')).toBeInTheDocument();
      expect(screen.getByText('Score: 15')).toBeInTheDocument();
      expect(screen.getByText(/add uppercase letters/i)).toBeInTheDocument();
      expect(screen.getByText(/add numbers/i)).toBeInTheDocument();
    });
  });

  it('displays weak strength correctly', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: {
        strength: 'weak',
        score: 35,
        suggestions: ['Avoid common passwords'],
      },
    } as any);

    render(<PasswordStrengthMeter password="password123" />);

    await waitFor(() => {
      expect(screen.getByText('Weak')).toBeInTheDocument();
      expect(screen.getByText('Score: 35')).toBeInTheDocument();
    });
  });

  it('displays medium strength correctly', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: {
        strength: 'medium',
        score: 60,
        suggestions: ['Use at least 12 characters for better security'],
      },
    } as any);

    render(<PasswordStrengthMeter password="MyPassword123" />);

    await waitFor(() => {
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText('Score: 60')).toBeInTheDocument();
    });
  });

  it('displays strong strength correctly', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: {
        strength: 'strong',
        score: 75,
        suggestions: ['Use at least 12 characters for better security'],
      },
    } as any);

    render(<PasswordStrengthMeter password="MyP@ssw0rd!" />);

    await waitFor(() => {
      expect(screen.getByText('Strong')).toBeInTheDocument();
      expect(screen.getByText('Score: 75')).toBeInTheDocument();
    });
  });

  it('displays very strong strength correctly', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: {
        strength: 'very_strong',
        score: 95,
        suggestions: ['Password is very strong!'],
      },
    } as any);

    render(<PasswordStrengthMeter password="MyV3ry$tr0ng&P@ssw0rd!" />);

    await waitFor(() => {
      expect(screen.getByText('Very Strong')).toBeInTheDocument();
      expect(screen.getByText('Score: 95')).toBeInTheDocument();
      expect(screen.getByText(/password is very strong/i)).toBeInTheDocument();
    });
  });

  it('calls onStrengthChange callback with strength data', async () => {
    const mockCallback = jest.fn();

    mockedApiClient.post.mockResolvedValue({
      data: {
        strength: 'strong',
        score: 80,
        suggestions: [],
      },
    } as any);

    render(
      <PasswordStrengthMeter
        password="StrongPass123!"
        onStrengthChange={mockCallback}
      />
    );

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith({
        strength: 'strong',
        score: 80,
        suggestions: [],
      });
    });
  });

  it('calls onStrengthChange with null for empty password', () => {
    const mockCallback = jest.fn();

    render(
      <PasswordStrengthMeter password="" onStrengthChange={mockCallback} />
    );

    expect(mockCallback).toHaveBeenCalledWith(null);
  });

  it('debounces API calls', async () => {
    const { rerender } = render(<PasswordStrengthMeter password="T" />);

    // Rapidly change password
    rerender(<PasswordStrengthMeter password="Te" />);
    rerender(<PasswordStrengthMeter password="Tes" />);
    rerender(<PasswordStrengthMeter password="Test" />);

    // Wait for debounce
    await waitFor(
      () => {
        // Should only call API once after debounce period
        expect(mockedApiClient.post).toHaveBeenCalledTimes(1);
      },
      { timeout: 500 }
    );
  });

  it('falls back to client-side check on API error', async () => {
    mockedApiClient.post.mockRejectedValue(new Error('Network error'));
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(<PasswordStrengthMeter password="FallbackTest123" />);

    await waitFor(() => {
      // Should still show strength (from client-side fallback)
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('renders correct number of bars for each strength level', async () => {
    const strengths = [
      { strength: 'very_weak', bars: 1 },
      { strength: 'weak', bars: 2 },
      { strength: 'medium', bars: 3 },
      { strength: 'strong', bars: 4 },
      { strength: 'very_strong', bars: 5 },
    ];

    for (const { strength, bars } of strengths) {
      mockedApiClient.post.mockResolvedValue({
        data: { strength, score: 50, suggestions: [] },
      } as any);

      const { container, rerender } = render(
        <PasswordStrengthMeter password={`test${strength}`} />
      );

      await waitFor(() => {
        const filledBars = container.querySelectorAll(
          '[class*="bg-red-500"], [class*="bg-orange-500"], [class*="bg-yellow-500"], [class*="bg-green-500"], [class*="bg-green-600"]'
        );
        expect(filledBars.length).toBe(bars);
      });

      rerender(<PasswordStrengthMeter password="" />);
    }
  });

  it('applies custom className', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: { strength: 'medium', score: 60, suggestions: [] },
    } as any);

    const { container } = render(
      <PasswordStrengthMeter password="test" className="custom-class" />
    );

    await waitFor(() => {
      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });
  });

  it('displays all suggestions', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: {
        strength: 'weak',
        score: 40,
        suggestions: [
          'Add uppercase letters',
          'Add special characters',
          'Use at least 12 characters',
        ],
      },
    } as any);

    render(<PasswordStrengthMeter password="test123" />);

    await waitFor(() => {
      expect(screen.getByText(/add uppercase letters/i)).toBeInTheDocument();
      expect(screen.getByText(/add special characters/i)).toBeInTheDocument();
      expect(screen.getByText(/use at least 12 characters/i)).toBeInTheDocument();
    });
  });
});
