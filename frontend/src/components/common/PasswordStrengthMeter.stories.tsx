/**
 * Storybook stories for PasswordStrengthMeter component
 */

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { PasswordStrengthMeter } from './PasswordStrengthMeter';

const meta: Meta<typeof PasswordStrengthMeter> = {
  title: 'Common/PasswordStrengthMeter',
  component: PasswordStrengthMeter,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Real-time password strength indicator with visual feedback and suggestions. Integrates with backend API for accurate strength calculation.',
      },
    },
  },
  decorators: [
    (Story) => (
      <div className="w-96 p-4">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof PasswordStrengthMeter>;

/**
 * Interactive example with input field
 */
export const Interactive: Story = {
  render: () => {
    const [password, setPassword] = useState('');

    return (
      <div className="space-y-4">
        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Enter Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Type a password..."
          />
        </div>
        <PasswordStrengthMeter password={password} />
      </div>
    );
  },
};

/**
 * Very weak password (short, no variety)
 */
export const VeryWeak: Story = {
  args: {
    password: 'abc',
  },
};

/**
 * Weak password (common password)
 */
export const Weak: Story = {
  args: {
    password: 'password123',
  },
};

/**
 * Medium password (meets basic requirements)
 */
export const Medium: Story = {
  args: {
    password: 'MyPassword123',
  },
};

/**
 * Strong password (good length and variety)
 */
export const Strong: Story = {
  args: {
    password: 'MyP@ssw0rd123!',
  },
};

/**
 * Very strong password (excellent)
 */
export const VeryStrong: Story = {
  args: {
    password: 'MyV3ry$tr0ng&L0ngP@ssw0rd!',
  },
};

/**
 * Empty password (no indicator shown)
 */
export const Empty: Story = {
  args: {
    password: '',
  },
};

/**
 * With callback example
 */
export const WithCallback: Story = {
  render: () => {
    const [password, setPassword] = useState('TestPass123');
    const [strengthInfo, setStrengthInfo] = useState<string>('');

    return (
      <div className="space-y-4">
        <div>
          <label
            htmlFor="password-callback"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Password
          </label>
          <input
            id="password-callback"
            type="text"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <PasswordStrengthMeter
          password={password}
          onStrengthChange={(strength) => {
            if (strength) {
              setStrengthInfo(
                `Strength: ${strength.strength}, Score: ${strength.score}`
              );
            } else {
              setStrengthInfo('No password entered');
            }
          }}
        />
        {strengthInfo && (
          <div className="p-3 bg-gray-100 rounded-md">
            <p className="text-sm text-gray-700">
              <strong>Callback Info:</strong> {strengthInfo}
            </p>
          </div>
        )}
      </div>
    );
  },
};

/**
 * Dark mode example
 */
export const DarkMode: Story = {
  render: () => {
    const [password, setPassword] = useState('MyP@ssw0rd123');

    return (
      <div className="dark bg-gray-900 p-6 rounded-lg">
        <div className="space-y-4">
          <div>
            <label
              htmlFor="password-dark"
              className="block text-sm font-medium text-gray-300 mb-1"
            >
              Password
            </label>
            <input
              id="password-dark"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Type a password..."
            />
          </div>
          <PasswordStrengthMeter password={password} />
        </div>
      </div>
    );
  },
  parameters: {
    backgrounds: { default: 'dark' },
  },
};

/**
 * Custom styling example
 */
export const CustomStyling: Story = {
  args: {
    password: 'CustomStyled123!',
    className: 'p-4 bg-blue-50 rounded-lg border border-blue-200',
  },
};
