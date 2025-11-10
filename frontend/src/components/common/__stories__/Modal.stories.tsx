import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { Modal } from '../Modal';
import { Button } from '../Button';
import { Input } from '../Input';

const meta = {
  title: 'Components/Common/Modal',
  component: Modal,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Modal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Basic: Story = {
  args: {
    isOpen: false,
    onClose: () => {},
    title: 'Modal',
    children: <p>Content</p>,
  },
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Open Modal</Button>
        <Modal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Basic Modal"
        >
          <p className="text-gray-600">
            This is a basic modal with a title and content.
          </p>
        </Modal>
      </>
    );
  },
};

export const WithForm: Story = {
  args: {
    isOpen: false,
    onClose: () => {},
    title: 'Modal',
    children: <p>Content</p>,
  },
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Create Agent</Button>
        <Modal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Create New Agent"
        >
          <div className="space-y-4">
            <Input label="Agent Name" placeholder="My Agent" />
            <Input label="Description" placeholder="Agent description" />
            <div className="flex justify-end space-x-2 mt-6">
              <Button variant="ghost" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={() => setIsOpen(false)}>
                Create
              </Button>
            </div>
          </div>
        </Modal>
      </>
    );
  },
};

export const LargeContent: Story = {
  args: {
    isOpen: false,
    onClose: () => {},
    title: 'Modal',
    children: <p>Content</p>,
  },
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <>
        <Button onClick={() => setIsOpen(true)}>View Details</Button>
        <Modal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Agent Configuration Details"
        >
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-gray-900">System Prompt</h4>
              <p className="text-sm text-gray-600 mt-2">
                You are a helpful AI assistant specialized in research and analysis.
                You have access to various tools and can help users with complex tasks.
                Always be clear, concise, and accurate in your responses.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Model Configuration</h4>
              <ul className="text-sm text-gray-600 mt-2 space-y-1">
                <li>Provider: Anthropic</li>
                <li>Model: claude-3-5-sonnet-20241022</li>
                <li>Temperature: 0.7</li>
                <li>Max Tokens: 4096</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Features</h4>
              <ul className="text-sm text-gray-600 mt-2 space-y-1">
                <li>Planning: Enabled</li>
                <li>Filesystem: Disabled</li>
              </ul>
            </div>
          </div>
        </Modal>
      </>
    );
  },
};

export const DeleteConfirmation: Story = {
  args: {
    isOpen: false,
    onClose: () => {},
    title: 'Modal',
    children: <p>Content</p>,
  },
  render: () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <>
        <Button variant="danger" onClick={() => setIsOpen(true)}>
          Delete Agent
        </Button>
        <Modal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Confirm Deletion"
        >
          <div className="space-y-4">
            <p className="text-gray-600">
              Are you sure you want to delete this agent? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-2">
              <Button variant="ghost" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button variant="danger" onClick={() => setIsOpen(false)}>
                Delete
              </Button>
            </div>
          </div>
        </Modal>
      </>
    );
  },
};
