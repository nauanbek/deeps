import type { Meta, StoryObj } from '@storybook/react';
import { ExecutionStatsChart } from '../ExecutionStatsChart';

const meta = {
  title: 'Components/Dashboard/ExecutionStatsChart',
  component: ExecutionStatsChart,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof ExecutionStatsChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const SevenDays: Story = {
  args: {
    stats: {
      by_status: {
        completed: 45,
        failed: 5,
        running: 2,
        pending: 3,
        cancelled: 1,
      },
      period_days: 7,
    },
  },
};

export const ThirtyDays: Story = {
  args: {
    stats: {
      by_status: {
        completed: 180,
        failed: 25,
        running: 5,
        pending: 10,
        cancelled: 8,
      },
      period_days: 30,
    },
  },
};

export const HighSuccessRate: Story = {
  args: {
    stats: {
      by_status: {
        completed: 95,
        failed: 2,
        running: 1,
        pending: 2,
        cancelled: 0,
      },
      period_days: 7,
    },
  },
};

export const ManyFailures: Story = {
  args: {
    stats: {
      by_status: {
        completed: 40,
        failed: 35,
        running: 3,
        pending: 5,
        cancelled: 10,
      },
      period_days: 7,
    },
  },
};

export const LowActivity: Story = {
  args: {
    stats: {
      by_status: {
        completed: 8,
        failed: 1,
        running: 0,
        pending: 1,
        cancelled: 0,
      },
      period_days: 7,
    },
  },
};

export const EmptyData: Story = {
  args: {
    stats: {
      by_status: {
        completed: 0,
        failed: 0,
        running: 0,
        pending: 0,
        cancelled: 0,
      },
      period_days: 7,
    },
  },
};
