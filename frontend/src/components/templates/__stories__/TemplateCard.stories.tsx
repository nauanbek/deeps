import type { Meta, StoryObj } from '@storybook/react';
import { TemplateCard, TemplateCardSkeleton } from '../TemplateCard';
import type { Template } from '../../../types/template';

const meta = {
  title: 'Components/Templates/TemplateCard',
  component: TemplateCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    onUseTemplate: { action: 'useTemplate' },
    onViewDetails: { action: 'viewDetails' },
  },
} satisfies Meta<typeof TemplateCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const baseTemplate: Template = {
  id: 1,
  name: 'Research Assistant',
  description: 'An AI agent specialized in conducting research and gathering information from various sources.',
  category: 'research',
  tags: ['research', 'analysis', 'information-gathering'],
  config_template: {
    model_provider: 'anthropic',
    model_name: 'claude-3-5-sonnet-20241022',
    system_prompt: 'You are a helpful research assistant.',
    temperature: 0.7,
    max_tokens: 4096,
    planning_enabled: true,
    filesystem_enabled: false,
    tool_ids: [],
  },
  is_public: true,
  is_featured: true,
  use_count: 156,
  created_by_id: 1,
  created_at: '2025-11-01T12:00:00Z',
  updated_at: '2025-11-10T01:00:00Z',
  is_active: true,
};

export const ResearchTemplate: Story = {
  args: {
    template: baseTemplate,
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const CodingTemplate: Story = {
  args: {
    template: {
      ...baseTemplate,
      id: 2,
      name: 'Code Assistant',
      description: 'Helps with coding tasks, code review, and software development best practices.',
      category: 'coding',
      tags: ['coding', 'development', 'code-review'],
      config_template: {
        ...baseTemplate.config_template,
        model_provider: 'openai',
        model_name: 'gpt-4',
        filesystem_enabled: true,
      },
      is_featured: false,
      use_count: 243,
    },
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const CustomerSupportTemplate: Story = {
  args: {
    template: {
      ...baseTemplate,
      id: 3,
      name: 'Customer Support Agent',
      description: 'Provides friendly and helpful customer support with access to knowledge base.',
      category: 'customer_support',
      tags: ['support', 'customer-service', 'helpdesk'],
      is_featured: false,
      use_count: 89,
    },
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const DataAnalysisTemplate: Story = {
  args: {
    template: {
      ...baseTemplate,
      id: 4,
      name: 'Data Analyst',
      description: 'Analyzes data, generates insights, and creates visualizations from datasets.',
      category: 'data_analysis',
      tags: ['data', 'analytics', 'visualization', 'insights'],
      use_count: 67,
    },
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const ContentWritingTemplate: Story = {
  args: {
    template: {
      ...baseTemplate,
      id: 5,
      name: 'Content Writer',
      description: 'Creates engaging content for blogs, articles, and social media posts.',
      category: 'content_writing',
      tags: ['writing', 'content', 'blog'],
      is_featured: true,
      use_count: 201,
    },
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const ManyTags: Story = {
  args: {
    template: {
      ...baseTemplate,
      id: 6,
      name: 'Swiss Army Agent',
      description: 'A versatile agent with many capabilities and tags.',
      category: 'general',
      tags: [
        'research',
        'coding',
        'analysis',
        'writing',
        'support',
        'documentation',
        'testing',
        'automation',
      ],
      use_count: 45,
    },
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const LongDescription: Story = {
  args: {
    template: {
      ...baseTemplate,
      id: 7,
      name: 'Documentation Generator',
      description:
        'This is a comprehensive documentation assistant that helps with creating, editing, and maintaining technical documentation for software projects. It can analyze code, generate API documentation, write tutorials, and ensure consistency across all documentation materials. The assistant is particularly skilled at understanding complex technical concepts and explaining them in clear, accessible language.',
      category: 'documentation',
      tags: ['documentation', 'technical-writing'],
      use_count: 112,
    },
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const LowUsage: Story = {
  args: {
    template: {
      ...baseTemplate,
      id: 8,
      name: 'New Template',
      description: 'A newly created template with minimal usage.',
      category: 'general',
      tags: ['new'],
      is_featured: false,
      use_count: 2,
    },
    onUseTemplate: (template) => console.log('Use template:', template),
    onViewDetails: (template) => console.log('View details:', template),
  },
};

export const LoadingSkeleton: StoryObj<typeof TemplateCardSkeleton> = {
  render: () => <TemplateCardSkeleton />,
  parameters: {
    docs: {
      description: {
        story: 'Loading skeleton displayed while template data is being fetched.',
      },
    },
  },
};
