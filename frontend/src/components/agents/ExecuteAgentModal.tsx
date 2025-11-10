import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateExecution } from '../../hooks/useExecutions';
import type { Agent } from '../../types/agent';

interface ExecuteAgentModalProps {
  agent: Agent;
  onClose: () => void;
}

export const ExecuteAgentModal: React.FC<ExecuteAgentModalProps> = ({
  agent,
  onClose,
}) => {
  const [prompt, setPrompt] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const createExecution = useCreateExecution();

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Prevent body scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) return;

    try {
      const execution = await createExecution.mutateAsync({
        agent_id: agent.id,
        input_text: trimmedPrompt,
      });

      // Navigate to execution monitor with auto-open details
      navigate(`/executions?execution=${execution.id}`);
      onClose();
    } catch (err) {
      console.error('Failed to create execution:', err);
      setError('Failed to start execution. Please try again.');
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const isValid = prompt.trim().length > 0;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
      data-testid="modal-backdrop"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full"
        onClick={(e) => e.stopPropagation()}
        data-testid="modal-content"
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Execute: {agent.name}
            </h2>
            {agent.description && (
              <p className="text-sm text-gray-600 mt-1">{agent.description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Configuration Preview */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Model:</span>
              <div className="font-medium text-gray-900">{agent.model_name}</div>
            </div>
            <div>
              <span className="text-gray-600">Temperature:</span>
              <div className="font-medium text-gray-900">{agent.temperature}</div>
            </div>
            <div>
              <span className="text-gray-600">Planning:</span>
              <div className="font-medium text-gray-900">
                {agent.planning_enabled ? 'Enabled' : 'Disabled'}
              </div>
            </div>
            <div>
              <span className="text-gray-600">Filesystem:</span>
              <div className="font-medium text-gray-900">
                {agent.filesystem_enabled ? 'Enabled' : 'Disabled'}
              </div>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Prompt
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt here..."
              rows={8}
              className="w-full px-3 py-2 border-gray-300 rounded-md shadow-sm focus-visible:ring-primary-500 focus-visible:border-primary-500"
              autoFocus
            />
            <div className="mt-1 text-xs text-gray-500">
              {prompt.length} characters
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border-gray-300 text-gray-700 rounded hover:bg-gray-50"
              disabled={createExecution.isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isValid || createExecution.isPending}
              className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createExecution.isPending ? 'Executing...' : 'Execute'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ExecuteAgentModal;
