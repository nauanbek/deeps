import { render, screen } from '@testing-library/react';
import { PlanViewer } from '../PlanViewer';

describe('PlanViewer', () => {
  test('renders plan with todos', () => {
    const plan = {
      todos: [
        { id: 1, description: 'Step 1', status: 'completed' as const },
        { id: 2, description: 'Step 2', status: 'in_progress' as const },
      ],
    };

    render(<PlanViewer plan={plan} />);

    expect(screen.getByText('Agent Plan')).toBeInTheDocument();
    expect(screen.getByText(/1\. Step 1/)).toBeInTheDocument();
    expect(screen.getByText(/2\. Step 2/)).toBeInTheDocument();
  });

  test('shows empty state when no todos', () => {
    const plan = { todos: [] };
    render(<PlanViewer plan={plan} />);
    expect(screen.getByText('No plan created yet')).toBeInTheDocument();
  });

  test('displays version when provided', () => {
    const plan = {
      todos: [{ id: 1, description: 'Task 1', status: 'pending' as const }],
      version: 3,
    };

    render(<PlanViewer plan={plan} />);
    expect(screen.getByText('v3')).toBeInTheDocument();
    expect(screen.getByLabelText('Plan version 3')).toBeInTheDocument();
  });

  test('displays correct status colors', () => {
    const plan = {
      todos: [
        { id: 1, description: 'Done', status: 'completed' as const },
        { id: 2, description: 'Working', status: 'in_progress' as const },
        { id: 3, description: 'Blocked', status: 'blocked' as const },
        { id: 4, description: 'Todo', status: 'pending' as const },
      ],
    };

    const { container } = render(<PlanViewer plan={plan} />);

    // Verify different status colors are applied
    expect(container.querySelector('.bg-green-100')).toBeInTheDocument();
    expect(container.querySelector('.bg-blue-100')).toBeInTheDocument();
    expect(container.querySelector('.bg-red-100')).toBeInTheDocument();
    expect(container.querySelector('.bg-gray-100')).toBeInTheDocument();
  });

  test('displays status icons correctly', () => {
    const plan = {
      todos: [
        { id: 1, description: 'Done', status: 'completed' as const },
        { id: 2, description: 'Working', status: 'in_progress' as const },
        { id: 3, description: 'Blocked', status: 'blocked' as const },
        { id: 4, description: 'Todo', status: 'pending' as const },
      ],
    };

    render(<PlanViewer plan={plan} />);

    // Check for status icons
    expect(screen.getByLabelText('Status: completed')).toHaveTextContent('✓');
    expect(screen.getByLabelText('Status: in_progress')).toHaveTextContent('⋯');
    expect(screen.getByLabelText('Status: blocked')).toHaveTextContent('✗');
    expect(screen.getByLabelText('Status: pending')).toHaveTextContent('○');
  });

  test('displays status text correctly', () => {
    const plan = {
      todos: [
        { id: 1, description: 'Task 1', status: 'in_progress' as const },
      ],
    };

    render(<PlanViewer plan={plan} />);
    // The actual text is lowercase, but CSS applies text-transform: uppercase
    expect(screen.getByText('in progress')).toBeInTheDocument();
  });

  test('handles todos without id', () => {
    const plan = {
      todos: [
        { id: 0, description: 'First task', status: 'pending' as const },
        { id: 0, description: 'Second task', status: 'pending' as const },
      ],
    };

    render(<PlanViewer plan={plan} />);

    // Should still render todos by index
    expect(screen.getByText(/1\. First task/)).toBeInTheDocument();
    expect(screen.getByText(/2\. Second task/)).toBeInTheDocument();
  });

  test('renders multiple todos in order', () => {
    const plan = {
      todos: [
        { id: 1, description: 'First', status: 'completed' as const },
        { id: 2, description: 'Second', status: 'in_progress' as const },
        { id: 3, description: 'Third', status: 'pending' as const },
      ],
    };

    const { container } = render(<PlanViewer plan={plan} />);
    const todoItems = container.querySelectorAll('[data-testid^="todo-item-"]');

    expect(todoItems).toHaveLength(3);
    expect(todoItems[0]).toHaveTextContent('1. First');
    expect(todoItems[1]).toHaveTextContent('2. Second');
    expect(todoItems[2]).toHaveTextContent('3. Third');
  });

  test('applies correct border colors for each status', () => {
    const plan = {
      todos: [
        { id: 1, description: 'Done', status: 'completed' as const },
        { id: 2, description: 'Working', status: 'in_progress' as const },
        { id: 3, description: 'Blocked', status: 'blocked' as const },
        { id: 4, description: 'Todo', status: 'pending' as const },
      ],
    };

    const { container } = render(<PlanViewer plan={plan} />);

    expect(container.querySelector('.border-green-200')).toBeInTheDocument();
    expect(container.querySelector('.border-blue-200')).toBeInTheDocument();
    expect(container.querySelector('.border-red-200')).toBeInTheDocument();
    expect(container.querySelector('.border-gray-200')).toBeInTheDocument();
  });

  test('handles long todo descriptions', () => {
    const plan = {
      todos: [
        {
          id: 1,
          description:
            'This is a very long todo description that should still be displayed properly without breaking the layout or causing any issues',
          status: 'pending' as const,
        },
      ],
    };

    render(<PlanViewer plan={plan} />);

    expect(
      screen.getByText(/This is a very long todo description/)
    ).toBeInTheDocument();
  });

  test('displays status labels with uppercase class', () => {
    const plan = {
      todos: [
        { id: 1, description: 'Task', status: 'in_progress' as const },
      ],
    };

    const { container } = render(<PlanViewer plan={plan} />);
    const statusLabel = container.querySelector('.uppercase');

    // The text content is lowercase, but CSS class applies uppercase styling
    expect(statusLabel).toHaveTextContent('in progress');
    expect(statusLabel).toHaveClass('uppercase');
  });
});
