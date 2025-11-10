import type { Meta, StoryObj } from '@storybook/react';
import { LoadingSpinner } from '../LoadingSpinner';

const meta = {
  title: 'Components/Common/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof LoadingSpinner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithText: Story = {
  render: () => (
    <div className="flex flex-col items-center space-y-4">
      <LoadingSpinner />
      <p className="text-gray-600">Loading data...</p>
    </div>
  ),
};

export const InCard: Story = {
  render: () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <div className="flex flex-col items-center justify-center space-y-4">
        <LoadingSpinner />
        <p className="text-gray-600">Fetching agent configurations...</p>
      </div>
    </div>
  ),
};

export const MultipleStates: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-8">
      <div className="flex flex-col items-center space-y-2">
        <LoadingSpinner />
        <p className="text-sm text-gray-600">Loading</p>
      </div>
      <div className="flex flex-col items-center space-y-2">
        <LoadingSpinner />
        <p className="text-sm text-gray-600">Processing</p>
      </div>
      <div className="flex flex-col items-center space-y-2">
        <LoadingSpinner />
        <p className="text-sm text-gray-600">Analyzing</p>
      </div>
    </div>
  ),
};
