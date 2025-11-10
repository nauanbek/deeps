import type { Meta, StoryObj } from '@storybook/react';
import { MetricCard } from '../MetricCard';
import {
  ChartBarIcon,
  ClockIcon,
  CpuChipIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';

const meta = {
  title: 'Components/Dashboard/MetricCard',
  component: MetricCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    onClick: { action: 'clicked' },
  },
} satisfies Meta<typeof MetricCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const TotalExecutions: Story = {
  args: {
    title: 'Total Executions',
    value: '1,234',
    subtitle: 'Last 30 days',
    icon: <ChartBarIcon className="w-6 h-6 text-primary-600" />,
    trend: {
      value: 12.5,
      isPositive: true,
    },
  },
};

export const AverageDuration: Story = {
  args: {
    title: 'Avg Duration',
    value: '2.4s',
    subtitle: 'Per execution',
    icon: <ClockIcon className="w-6 h-6 text-blue-600" />,
    trend: {
      value: 8.3,
      isPositive: false,
    },
  },
};

export const ActiveAgents: Story = {
  args: {
    title: 'Active Agents',
    value: 12,
    icon: <CpuChipIcon className="w-6 h-6 text-green-600" />,
  },
};

export const TotalCost: Story = {
  args: {
    title: 'Total Cost',
    value: '$45.67',
    subtitle: 'This month',
    icon: <CurrencyDollarIcon className="w-6 h-6 text-purple-600" />,
    trend: {
      value: 15.2,
      isPositive: true,
    },
  },
};

export const WithoutTrend: Story = {
  args: {
    title: 'Success Rate',
    value: '98.5%',
    subtitle: 'All time',
    icon: <ChartBarIcon className="w-6 h-6 text-emerald-600" />,
  },
};

export const WithoutSubtitle: Story = {
  args: {
    title: 'Running Tasks',
    value: 5,
    icon: <CpuChipIcon className="w-6 h-6 text-orange-600" />,
    trend: {
      value: 25,
      isPositive: true,
    },
  },
};

export const Clickable: Story = {
  args: {
    title: 'Failed Executions',
    value: 3,
    subtitle: 'Requires attention',
    icon: <ChartBarIcon className="w-6 h-6 text-red-600" />,
    onClick: () => console.log('Navigate to failures'),
  },
};

export const NegativeTrend: Story = {
  args: {
    title: 'Token Usage',
    value: '1.2M',
    subtitle: 'Last 7 days',
    icon: <CpuChipIcon className="w-6 h-6 text-indigo-600" />,
    trend: {
      value: 22.1,
      isPositive: false,
    },
  },
};

export const LargeNumber: Story = {
  args: {
    title: 'Total Tokens',
    value: '12,345,678',
    subtitle: 'All time',
    icon: <ChartBarIcon className="w-6 h-6 text-cyan-600" />,
    trend: {
      value: 105.5,
      isPositive: true,
    },
  },
};
