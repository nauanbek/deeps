import type { Meta, StoryObj } from '@storybook/react';
import { PlanViewer } from '../PlanViewer';

const meta = {
  title: 'Components/Executions/PlanViewer',
  component: PlanViewer,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof PlanViewer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const InProgress: Story = {
  args: {
    plan: {
      todos: [
        {
          id: 1,
          description: 'Research latest AI developments',
          status: 'completed',
        },
        {
          id: 2,
          description: 'Analyze findings and extract key insights',
          status: 'in_progress',
        },
        {
          id: 3,
          description: 'Generate comprehensive summary report',
          status: 'pending',
        },
        {
          id: 4,
          description: 'Review and validate final output',
          status: 'pending',
        },
      ],
      version: 1,
    },
  },
};

export const AllCompleted: Story = {
  args: {
    plan: {
      todos: [
        {
          id: 1,
          description: 'Load data from database',
          status: 'completed',
        },
        {
          id: 2,
          description: 'Process and transform data',
          status: 'completed',
        },
        {
          id: 3,
          description: 'Generate visualization charts',
          status: 'completed',
        },
      ],
      version: 1,
    },
  },
};

export const JustStarted: Story = {
  args: {
    plan: {
      todos: [
        {
          id: 1,
          description: 'Initialize project structure',
          status: 'in_progress',
        },
        {
          id: 2,
          description: 'Set up configuration files',
          status: 'pending',
        },
        {
          id: 3,
          description: 'Install dependencies',
          status: 'pending',
        },
      ],
      version: 1,
    },
  },
};

export const ManyTasks: Story = {
  args: {
    plan: {
      todos: [
        {
          id: 1,
          description: 'Task 1: Complete initial setup',
          status: 'completed',
        },
        {
          id: 2,
          description: 'Task 2: Configure environment',
          status: 'completed',
        },
        {
          id: 3,
          description: 'Task 3: Build initial prototype',
          status: 'completed',
        },
        {
          id: 4,
          description: 'Task 4: Test prototype functionality',
          status: 'in_progress',
        },
        {
          id: 5,
          description: 'Task 5: Refactor code structure',
          status: 'pending',
        },
        {
          id: 6,
          description: 'Task 6: Add error handling',
          status: 'pending',
        },
        {
          id: 7,
          description: 'Task 7: Write documentation',
          status: 'pending',
        },
        {
          id: 8,
          description: 'Task 8: Deploy to production',
          status: 'pending',
        },
      ],
      version: 2,
    },
  },
};

export const SingleTask: Story = {
  args: {
    plan: {
      todos: [
        {
          id: 1,
          description: 'Execute simple query and return results',
          status: 'completed',
        },
      ],
      version: 1,
    },
  },
};
