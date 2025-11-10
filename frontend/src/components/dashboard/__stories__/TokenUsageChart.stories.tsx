import type { Meta, StoryObj } from '@storybook/react';
import { TokenUsageChart } from '../TokenUsageChart';

const meta = {
  title: 'Components/Dashboard/TokenUsageChart',
  component: TokenUsageChart,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof TokenUsageChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const SevenDays: Story = {
  args: {
    usage: {
      total_tokens: 250000,
      prompt_tokens: 150000,
      completion_tokens: 100000,
      estimated_cost: 25.5,
      period_days: 7,
    },
  },
};

export const ThirtyDays: Story = {
  args: {
    usage: {
      total_tokens: 1500000,
      prompt_tokens: 900000,
      completion_tokens: 600000,
      estimated_cost: 152.8,
      period_days: 30,
    },
  },
};

export const LowUsage: Story = {
  args: {
    usage: {
      total_tokens: 8500,
      prompt_tokens: 5000,
      completion_tokens: 3500,
      estimated_cost: 0.92,
      period_days: 7,
    },
  },
};

export const HighUsage: Story = {
  args: {
    usage: {
      total_tokens: 750000,
      prompt_tokens: 450000,
      completion_tokens: 300000,
      estimated_cost: 76.5,
      period_days: 7,
    },
  },
};

export const EmptyData: Story = {
  args: {
    usage: {
      total_tokens: 0,
      prompt_tokens: 0,
      completion_tokens: 0,
      estimated_cost: 0,
      period_days: 7,
    },
  },
};
