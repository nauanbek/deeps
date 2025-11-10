import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader } from '../Card';
import { Button } from '../Button';
import { PlusIcon } from '@heroicons/react/24/outline';

const meta = {
  title: 'Components/Common/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: (
      <div>
        <h3 className="text-lg font-semibold mb-2">Card Title</h3>
        <p className="text-gray-600">This is a basic card with default medium padding.</p>
      </div>
    ),
  },
};

export const SmallPadding: Story = {
  args: {
    padding: 'sm',
    children: (
      <div>
        <h3 className="text-lg font-semibold mb-2">Small Padding</h3>
        <p className="text-gray-600">This card uses small padding (p-4).</p>
      </div>
    ),
  },
};

export const LargePadding: Story = {
  args: {
    padding: 'lg',
    children: (
      <div>
        <h3 className="text-lg font-semibold mb-2">Large Padding</h3>
        <p className="text-gray-600">This card uses large padding (p-8).</p>
      </div>
    ),
  },
};

export const NoPadding: Story = {
  args: {
    padding: 'none',
    children: (
      <div className="p-4">
        <h3 className="text-lg font-semibold mb-2">No Padding</h3>
        <p className="text-gray-600">This card has no padding from Card component. Padding is manually applied.</p>
      </div>
    ),
  },
};

export const WithHeader: Story = {
  args: {
    children: (
      <>
        <CardHeader title="Card with Header" subtitle="This demonstrates the CardHeader component" />
        <p className="text-gray-600">Card content goes here...</p>
      </>
    ),
  },
};

export const WithHeaderAction: Story = {
  args: {
    children: (
      <>
        <CardHeader
          title="User Settings"
          subtitle="Manage your account preferences"
          action={
            <Button variant="primary" size="sm">
              <PlusIcon className="w-4 h-4 mr-1" />
              Add New
            </Button>
          }
        />
        <div className="space-y-2">
          <div className="flex items-center justify-between py-2 border-b border-gray-200">
            <span className="text-sm text-gray-700">Email notifications</span>
            <span className="text-sm font-medium text-gray-900">Enabled</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-200">
            <span className="text-sm text-gray-700">Dark mode</span>
            <span className="text-sm font-medium text-gray-900">Disabled</span>
          </div>
        </div>
      </>
    ),
  },
};

export const ComplexContent: Story = {
  args: {
    children: (
      <>
        <CardHeader title="Agent Metrics" subtitle="Last 30 days" />
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">156</p>
            <p className="text-sm text-gray-600">Executions</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">98.5%</p>
            <p className="text-sm text-gray-600">Success Rate</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">2.4s</p>
            <p className="text-sm text-gray-600">Avg Duration</p>
          </div>
        </div>
      </>
    ),
  },
};

export const WithCustomClass: Story = {
  args: {
    className: 'border-2 border-primary-500 shadow-lg',
    children: (
      <div>
        <h3 className="text-lg font-semibold mb-2 text-primary-700">Featured Card</h3>
        <p className="text-gray-600">This card has custom border and shadow classes.</p>
      </div>
    ),
  },
};

export const MultipleCards: Story = {
  args: {
    children: <p>Card content</p>,
  },
  render: () => (
    <div className="grid gap-4" style={{ width: '600px' }}>
      <Card>
        <CardHeader title="Card 1" />
        <p className="text-gray-600">First card content</p>
      </Card>
      <Card>
        <CardHeader title="Card 2" />
        <p className="text-gray-600">Second card content</p>
      </Card>
      <Card>
        <CardHeader title="Card 3" />
        <p className="text-gray-600">Third card content</p>
      </Card>
    </div>
  ),
};
