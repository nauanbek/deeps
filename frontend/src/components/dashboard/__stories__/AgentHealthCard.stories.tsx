import type { Meta, StoryObj } from '@storybook/react';
import { AgentHealthCard } from '../AgentHealthCard';

const meta = {
  title: 'Components/Dashboard/AgentHealthCard',
  component: AgentHealthCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof AgentHealthCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Healthy: Story = {
  args: {
    health: {
      agent_id: 1,
      agent_name: 'Research Assistant',
      total_executions: 150,
      success_count: 148,
      error_count: 2,
      success_rate: 98.5,
      avg_execution_time: 2.3,
      last_execution_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    },
  },
};

export const Warning: Story = {
  args: {
    health: {
      agent_id: 2,
      agent_name: 'Code Assistant',
      total_executions: 200,
      success_count: 170,
      error_count: 30,
      success_rate: 85.0,
      avg_execution_time: 5.7,
      last_execution_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    },
  },
};

export const Error: Story = {
  args: {
    health: {
      agent_id: 3,
      agent_name: 'Data Processor',
      total_executions: 100,
      success_count: 45,
      error_count: 55,
      success_rate: 45.0,
      avg_execution_time: 12.4,
      last_execution_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    },
  },
};

export const Idle: Story = {
  args: {
    health: {
      agent_id: 4,
      agent_name: 'Documentation Generator',
      total_executions: 0,
      success_count: 0,
      error_count: 0,
      success_rate: 0,
      avg_execution_time: 0,
      last_execution_at: null,
    },
  },
};

export const PerfectScore: Story = {
  args: {
    health: {
      agent_id: 5,
      agent_name: 'Customer Support Bot',
      total_executions: 50,
      success_count: 50,
      error_count: 0,
      success_rate: 100,
      avg_execution_time: 1.2,
      last_execution_at: new Date().toISOString(),
    },
  },
};
