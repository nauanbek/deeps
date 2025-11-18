/**
 * PasswordStrengthMeter Component
 *
 * Real-time password strength indicator with visual feedback and suggestions.
 * Integrates with backend /api/v1/auth/check-password-strength endpoint.
 *
 * Features:
 * - Color-coded strength indicator (red -> yellow -> green)
 * - Numeric strength score display
 * - Actionable improvement suggestions
 * - Debounced API calls (300ms)
 * - Supports light/dark mode via Tailwind
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';

export interface PasswordStrength {
  strength: 'very_weak' | 'weak' | 'medium' | 'strong' | 'very_strong';
  score: number;
  suggestions: string[];
}

interface PasswordStrengthMeterProps {
  password: string;
  onStrengthChange?: (strength: PasswordStrength | null) => void;
  className?: string;
}

const strengthConfig = {
  very_weak: {
    label: 'Very Weak',
    color: 'bg-red-500',
    textColor: 'text-red-600',
    bars: 1,
  },
  weak: {
    label: 'Weak',
    color: 'bg-orange-500',
    textColor: 'text-orange-600',
    bars: 2,
  },
  medium: {
    label: 'Medium',
    color: 'bg-yellow-500',
    textColor: 'text-yellow-600',
    bars: 3,
  },
  strong: {
    label: 'Strong',
    color: 'bg-green-500',
    textColor: 'text-green-600',
    bars: 4,
  },
  very_strong: {
    label: 'Very Strong',
    color: 'bg-green-600',
    textColor: 'text-green-700',
    bars: 5,
  },
};

/**
 * Password Strength Meter Component
 *
 * @param password - Current password value
 * @param onStrengthChange - Callback when strength changes
 * @param className - Additional CSS classes
 */
export const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({
  password,
  onStrengthChange,
  className = '',
}) => {
  const [strength, setStrength] = useState<PasswordStrength | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Don't check empty passwords
    if (!password || password.length === 0) {
      setStrength(null);
      onStrengthChange?.(null);
      return;
    }

    // Debounce API calls
    const timeoutId = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await apiClient.post<PasswordStrength>(
          '/auth/check-password-strength',
          { password }
        );
        setStrength(response.data);
        onStrengthChange?.(response.data);
      } catch (error) {
        console.error('Failed to check password strength:', error);
        // Fallback to basic client-side check
        const basicStrength = getBasicStrength(password);
        setStrength(basicStrength);
        onStrengthChange?.(basicStrength);
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [password, onStrengthChange]);

  // Don't render if no password
  if (!password || password.length === 0) {
    return null;
  }

  // Show loading state
  if (loading && !strength) {
    return (
      <div className={`space-y-2 ${className}`}>
        <div className="flex space-x-1">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="h-2 flex-1 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
            />
          ))}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Checking password strength...
        </p>
      </div>
    );
  }

  if (!strength) {
    return null;
  }

  const config = strengthConfig[strength.strength];

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Strength Bars */}
      <div className="flex space-x-1" role="progressbar" aria-valuenow={strength.score}>
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className={`h-2 flex-1 rounded ${
              i < config.bars
                ? config.color
                : 'bg-gray-200 dark:bg-gray-700'
            }`}
          />
        ))}
      </div>

      {/* Strength Label and Score */}
      <div className="flex items-center justify-between">
        <span
          className={`text-sm font-medium ${config.textColor} dark:${config.textColor}`}
        >
          {config.label}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          Score: {strength.score}
        </span>
      </div>

      {/* Suggestions */}
      {strength.suggestions.length > 0 && (
        <div className="space-y-1">
          {strength.suggestions.map((suggestion, index) => (
            <p
              key={index}
              className="text-xs text-gray-600 dark:text-gray-400 flex items-start"
            >
              <span className="mr-1">
                {strength.strength === 'very_strong' ? '✓' : '•'}
              </span>
              <span>{suggestion}</span>
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Basic client-side password strength check (fallback)
 */
function getBasicStrength(password: string): PasswordStrength {
  let score = 0;
  const suggestions: string[] = [];

  // Length scoring
  score += Math.min(password.length, 20);

  // Character variety
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasDigit = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*()_+\-=[\]{}|;:,.<>?/~`]/.test(password);

  if (hasUpper) score += 10;
  else suggestions.push('Add uppercase letters');

  if (hasLower) score += 10;
  else suggestions.push('Add lowercase letters');

  if (hasDigit) score += 10;
  else suggestions.push('Add numbers');

  if (hasSpecial) score += 15;
  else suggestions.push('Add special characters (!@#$%^&*)');

  if (password.length > 12) score += 10;
  else suggestions.push('Use at least 12 characters for better security');

  // Determine strength
  let strength: PasswordStrength['strength'];
  if (score < 30) strength = 'very_weak';
  else if (score < 50) strength = 'weak';
  else if (score < 70) strength = 'medium';
  else if (score < 90) strength = 'strong';
  else strength = 'very_strong';

  return { strength, score, suggestions };
}

export default PasswordStrengthMeter;
