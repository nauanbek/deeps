import type { Meta, StoryObj } from '@storybook/react';
import { Select } from '../Select';

const meta = {
  title: 'Components/Common/Select',
  component: Select,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: 'Model Provider',
    options: [
      { value: 'anthropic', label: 'Anthropic' },
      { value: 'openai', label: 'OpenAI' },
    ],
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Agent Category',
    helperText: 'Select the category that best describes your agent',
    options: [
      { value: 'research', label: 'Research' },
      { value: 'coding', label: 'Coding' },
      { value: 'customer_support', label: 'Customer Support' },
      { value: 'data_analysis', label: 'Data Analysis' },
    ],
  },
};

export const WithError: Story = {
  args: {
    label: 'Model Name',
    error: 'This field is required',
    options: [
      { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
      { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
      { value: 'gpt-4', label: 'GPT-4' },
    ],
  },
};

export const ManyOptions: Story = {
  args: {
    label: 'Template',
    placeholder: 'Select a template...',
    options: [
      { value: '1', label: 'Research Assistant' },
      { value: '2', label: 'Code Assistant' },
      { value: '3', label: 'Customer Support Agent' },
      { value: '4', label: 'Data Analyst' },
      { value: '5', label: 'Content Writer' },
      { value: '6', label: 'Code Reviewer' },
      { value: '7', label: 'Documentation Generator' },
      { value: '8', label: 'Test Automation Agent' },
    ],
  },
};

export const Required: Story = {
  args: {
    label: 'Status',
    required: true,
    options: [
      { value: 'active', label: 'Active' },
      { value: 'inactive', label: 'Inactive' },
    ],
  },
};

export const Disabled: Story = {
  args: {
    label: 'Region',
    disabled: true,
    options: [
      { value: 'us-east-1', label: 'US East 1' },
      { value: 'us-west-2', label: 'US West 2' },
    ],
  },
};

export const AllStates: Story = {
  render: () => (
    <div className="space-y-6" style={{ width: '400px' }}>
      <Select
        label="Default"
        options={[
          { value: '1', label: 'Option 1' },
          { value: '2', label: 'Option 2' },
        ]}
      />
      <Select
        label="With Helper Text"
        helperText="Choose one option"
        options={[
          { value: '1', label: 'Option 1' },
          { value: '2', label: 'Option 2' },
        ]}
      />
      <Select
        label="With Error"
        error="This field is required"
        options={[
          { value: '1', label: 'Option 1' },
          { value: '2', label: 'Option 2' },
        ]}
      />
      <Select
        label="Disabled"
        disabled
        options={[
          { value: '1', label: 'Option 1' },
          { value: '2', label: 'Option 2' },
        ]}
      />
    </div>
  ),
};
