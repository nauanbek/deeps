import type { Meta, StoryObj } from '@storybook/react';
import { AgentCard, AgentCardSkeleton } from '../AgentCard';
import type { Agent } from '../../../types/agent';

const meta = {
  title: 'Components/Agents/AgentCard',
  component: AgentCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    onEdit: { action: 'edit' },
    onDelete: { action: 'delete' },
    onExecute: { action: 'execute' },
    onAdvancedConfig: { action: 'advancedConfig' },
    onManageTools: { action: 'manageTools' },
  },
} satisfies Meta<typeof AgentCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const baseAgent: Agent = {
  id: 1,
  name: 'Research Assistant',
  description: 'An AI agent specialized in conducting research and gathering information from various sources.',
  system_prompt: 'You are a helpful research assistant.',
  model_provider: 'anthropic',
  model_name: 'claude-3-5-sonnet-20241022',
  temperature: 0.7,
  max_tokens: 4096,
  planning_enabled: true,
  filesystem_enabled: false,
  additional_config: {},
  is_active: true,
  created_by_id: 1,
  created_at: '2025-11-09T12:00:00Z',
  updated_at: '2025-11-10T01:00:00Z',
};

export const Active: Story = {
  args: {
    agent: baseAgent,
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
    onExecute: (agentId) => console.log('Execute agent:', agentId),
    onAdvancedConfig: (agent) => console.log('Advanced config for:', agent),
    onManageTools: (agent) => console.log('Manage tools for:', agent),
  },
};

export const Inactive: Story = {
  args: {
    agent: {
      ...baseAgent,
      id: 2,
      name: 'Code Assistant',
      description: 'Helps with coding tasks, code review, and software development.',
      is_active: false,
    },
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
  },
};

export const WithFilesystem: Story = {
  args: {
    agent: {
      ...baseAgent,
      id: 3,
      name: 'File Manager',
      description: 'Manages files and directories with full filesystem access.',
      planning_enabled: true,
      filesystem_enabled: true,
    },
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
  },
};

export const OpenAIModel: Story = {
  args: {
    agent: {
      ...baseAgent,
      id: 4,
      name: 'GPT-4 Assistant',
      description: 'Powered by OpenAI GPT-4 for general-purpose tasks.',
      model_provider: 'openai',
      model_name: 'gpt-4',
      temperature: 0.5,
      max_tokens: 8000,
    },
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
  },
};

export const NoFeatures: Story = {
  args: {
    agent: {
      ...baseAgent,
      id: 5,
      name: 'Simple Assistant',
      description: 'A basic assistant without planning or filesystem features.',
      planning_enabled: false,
      filesystem_enabled: false,
    },
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
  },
};

export const LongDescription: Story = {
  args: {
    agent: {
      ...baseAgent,
      id: 6,
      name: 'Documentation Assistant',
      description:
        'This is a comprehensive documentation assistant that helps with creating, editing, and maintaining technical documentation for software projects. It can analyze code, generate API documentation, write tutorials, and ensure consistency across all documentation materials. The assistant is particularly skilled at understanding complex technical concepts and explaining them in clear, accessible language.',
    },
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
  },
};

export const NoDescription: Story = {
  args: {
    agent: {
      ...baseAgent,
      id: 7,
      name: 'Minimal Agent',
      description: null,
    },
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
  },
};

export const WithoutExecuteAction: Story = {
  args: {
    agent: baseAgent,
    onEdit: (agent) => console.log('Edit agent:', agent),
    onDelete: (agentId) => console.log('Delete agent:', agentId),
    // onExecute is undefined
  },
};

export const LoadingSkeleton: StoryObj<typeof AgentCardSkeleton> = {
  render: () => <AgentCardSkeleton />,
  parameters: {
    docs: {
      description: {
        story: 'Loading skeleton displayed while agent data is being fetched.',
      },
    },
  },
};
