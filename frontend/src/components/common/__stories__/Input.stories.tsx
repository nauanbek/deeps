import type { Meta, StoryObj } from '@storybook/react';
import { Input } from '../Input';
import { MagnifyingGlassIcon, EnvelopeIcon, LockClosedIcon, UserIcon } from '@heroicons/react/24/outline';

const meta = {
  title: 'Components/Common/Input',
  component: Input,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
};

export const WithLabel: Story = {
  args: {
    label: 'Full Name',
    placeholder: 'John Doe',
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Email Address',
    placeholder: 'you@example.com',
    helperText: 'We will never share your email with anyone else.',
    type: 'email',
  },
};

export const WithError: Story = {
  args: {
    label: 'Password',
    type: 'password',
    placeholder: 'Enter password',
    error: 'Password must be at least 8 characters',
  },
};

export const WithLeftIcon: Story = {
  args: {
    label: 'Search',
    placeholder: 'Search agents...',
    icon: <MagnifyingGlassIcon className="w-5 h-5" />,
    iconPosition: 'left',
  },
};

export const WithRightIcon: Story = {
  args: {
    label: 'Username',
    placeholder: 'username',
    icon: <UserIcon className="w-5 h-5" />,
    iconPosition: 'right',
  },
};

export const EmailInput: Story = {
  args: {
    label: 'Email',
    type: 'email',
    placeholder: 'you@example.com',
    icon: <EnvelopeIcon className="w-5 h-5" />,
    iconPosition: 'left',
  },
};

export const PasswordInput: Story = {
  args: {
    label: 'Password',
    type: 'password',
    placeholder: 'Enter your password',
    icon: <LockClosedIcon className="w-5 h-5" />,
    iconPosition: 'left',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Read Only Field',
    value: 'This field is disabled',
    disabled: true,
  },
};

export const Required: Story = {
  args: {
    label: 'Agent Name',
    placeholder: 'My Agent',
    required: true,
  },
};

export const NumberInput: Story = {
  args: {
    label: 'Temperature',
    type: 'number',
    placeholder: '0.7',
    min: '0',
    max: '2',
    step: '0.1',
    helperText: 'Value between 0 and 2',
  },
};

export const LongLabel: Story = {
  args: {
    label: 'System Prompt for AI Agent Configuration',
    placeholder: 'You are a helpful assistant...',
  },
};

export const AllStates: Story = {
  render: () => (
    <div className="space-y-6" style={{ width: '400px' }}>
      <Input label="Default" placeholder="Default input" />
      <Input
        label="With Helper Text"
        placeholder="Enter value"
        helperText="This is a helpful hint"
      />
      <Input
        label="With Error"
        placeholder="Enter value"
        error="This field is required"
      />
      <Input
        label="With Icon"
        placeholder="Search..."
        icon={<MagnifyingGlassIcon className="w-5 h-5" />}
      />
      <Input label="Disabled" placeholder="Disabled" disabled />
    </div>
  ),
};
