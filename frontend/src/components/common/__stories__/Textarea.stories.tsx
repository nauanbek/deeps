import type { Meta, StoryObj } from '@storybook/react';
import { Textarea } from '../Textarea';

const meta = {
  title: 'Components/Common/Textarea',
  component: Textarea,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: 'Enter your text here...',
  },
};

export const WithLabel: Story = {
  args: {
    label: 'System Prompt',
    placeholder: 'You are a helpful assistant...',
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Agent Description',
    placeholder: 'Describe what this agent does...',
    helperText: 'Provide a detailed description to help users understand the agent purpose.',
  },
};

export const WithError: Story = {
  args: {
    label: 'Configuration',
    placeholder: 'Enter configuration...',
    error: 'This field is required',
  },
};

export const WithRows: Story = {
  args: {
    label: 'Long Content',
    placeholder: 'Enter long content here...',
    rows: 10,
  },
};

export const Disabled: Story = {
  args: {
    label: 'Read Only',
    value: 'This textarea is disabled and cannot be edited.',
    disabled: true,
  },
};

export const Required: Story = {
  args: {
    label: 'Feedback',
    placeholder: 'Please provide your feedback...',
    required: true,
  },
};

export const MaxLength: Story = {
  args: {
    label: 'Short Description',
    placeholder: 'Maximum 100 characters...',
    maxLength: 100,
    helperText: 'Maximum 100 characters',
  },
};

export const AllStates: Story = {
  render: () => (
    <div className="space-y-6" style={{ width: '600px' }}>
      <Textarea label="Default" placeholder="Default textarea" />
      <Textarea
        label="With Helper Text"
        placeholder="Enter value"
        helperText="This is a helpful hint"
      />
      <Textarea
        label="With Error"
        placeholder="Enter value"
        error="This field is required"
      />
      <Textarea label="Disabled" placeholder="Disabled" disabled />
      <Textarea
        label="Large"
        placeholder="Large textarea"
        rows={8}
      />
    </div>
  ),
};
