import React from 'react';

/**
 * Todo item in an agent plan
 */
interface Todo {
  id: number;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
}

/**
 * Plan data structure
 */
interface Plan {
  todos: Todo[];
  version?: number;
}

interface PlanViewerProps {
  plan: Plan;
}

/**
 * PlanViewer Component
 *
 * Displays an agent's execution plan created using the write_todos planning tool.
 * Shows todos with their status (pending, in_progress, completed, blocked).
 *
 * Features:
 * - Color-coded status badges
 * - Status icons for visual clarity
 * - Version tracking
 * - Empty state handling
 *
 * @param plan - The plan object containing todos and optional version
 */
export const PlanViewer: React.FC<PlanViewerProps> = ({ plan }) => {
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'blocked':
        return 'bg-red-100 text-red-800 border-red-200';
      default: // pending
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '⋯';
      case 'blocked':
        return '✗';
      default: // pending
        return '○';
    }
  };

  return (
    <div className="bg-white rounded-lg border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-900">Agent Plan</h4>
        {plan.version && (
          <span className="text-xs text-gray-500" aria-label={`Plan version ${plan.version}`}>
            v{plan.version}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {plan.todos.map((todo, index) => (
          <div
            key={todo.id || index}
            className={`flex items-start space-x-3 p-3 rounded ${getStatusColor(
              todo.status
            )}`}
            data-testid={`todo-item-${index}`}
          >
            <span className="text-lg font-medium mt-0.5" aria-label={`Status: ${todo.status}`}>
              {getStatusIcon(todo.status)}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium">
                {index + 1}. {todo.description}
              </p>
            </div>
            <span className="text-xs font-medium uppercase whitespace-nowrap">
              {todo.status.replace('_', ' ')}
            </span>
          </div>
        ))}
      </div>

      {plan.todos.length === 0 && (
        <p className="text-center text-gray-500 py-4 text-sm">No plan created yet</p>
      )}
    </div>
  );
};

export default PlanViewer;
