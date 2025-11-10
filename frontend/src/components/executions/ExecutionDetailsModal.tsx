import React, { useEffect, useRef, useMemo } from 'react';
import {
  useExecution,
  useExecutionTraces,
  useCancelExecution,
} from '../../hooks/useExecutions';
import { useExecutionWebSocket } from '../../hooks/useExecutionWebSocket';
import { TraceItem } from './TraceItem';
import { PlanViewer } from './PlanViewer';
import FilesystemViewer from './FilesystemViewer';
import { Loading } from '../common/Loading';
import { formatRelativeTime, formatDuration, formatNumber } from '../../utils/formatting';
import { STATUS_COLORS } from '../../utils/constants';

interface ExecutionDetailsModalProps {
  executionId: number;
  onClose: () => void;
}

export const ExecutionDetailsModal: React.FC<ExecutionDetailsModalProps> = ({
  executionId,
  onClose,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const tracesEndRef = useRef<HTMLDivElement>(null);

  // Fetch execution details
  const { data: execution, isLoading, isError } = useExecution(executionId);

  // Fetch initial traces
  const { data: initialTraces = [] } = useExecutionTraces(executionId);

  // Connect to WebSocket for live updates
  const {
    traces: wsTraces,
    isConnected,
    error: wsError,
  } = useExecutionWebSocket(executionId);

  // Cancel execution mutation
  const cancelExecution = useCancelExecution();

  // === TRACE DEDUPLICATION ALGORITHM ===
  // Combines initial HTTP-fetched traces with real-time WebSocket traces.
  //
  // Problem: When modal opens, we:
  //   1. Fetch initial traces via HTTP (historical data)
  //   2. Connect WebSocket for live updates (new traces)
  //   → Risk of duplicates if WebSocket sends traces we already have
  //
  // Solution: Merge both sources and deduplicate by sequence_number
  //
  // Example timeline:
  //   HTTP fetch returns: [trace#1, trace#2, trace#3]
  //   WebSocket sends:    [trace#3, trace#4, trace#5]  (overlap at trace#3)
  //   After merge:        [trace#1, trace#2, trace#3, trace#4, trace#5]
  //
  // Time complexity: O(n) where n = total traces
  // Space complexity: O(n) for the Set
  // === END ALGORITHM ===
  const allTraces = useMemo(() => {
    // STEP 1: Combine both arrays (may contain duplicates)
    const combined = [...initialTraces, ...wsTraces];

    // STEP 2: Deduplicate using Set to track seen sequence_numbers
    // sequence_number is a unique monotonic counter per execution
    const seen = new Set<number>();

    return combined.filter((trace) => {
      // If we've already seen this sequence_number, skip it
      if (seen.has(trace.sequence_number)) return false;

      // First time seeing this sequence_number - keep it and mark as seen
      seen.add(trace.sequence_number);
      return true;
    });
  }, [initialTraces, wsTraces]);

  // === PLAN EXTRACTION FROM TRACES ===
  // Extracts planning data (todos/tasks) from execution traces.
  //
  // Background: When agents use the write_todos tool, they emit 'plan_update' traces
  // containing the current task list. Plans can be updated multiple times during execution.
  //
  // Example trace flow:
  //   trace#5: plan_update → {todos: [{task: "Analyze data", status: "pending"}]}
  //   trace#12: plan_update → {todos: [{task: "Analyze data", status: "in_progress"}]}
  //   trace#20: plan_update → {todos: [{task: "Analyze data", status: "completed"}]}
  //
  // We need the LATEST version to show current progress.
  // === END CONTEXT ===

  // STEP 1: Filter all traces to get only plan_update events
  const planTraces = useMemo(() => {
    return allTraces.filter((trace) => trace.event_type === 'plan_update');
  }, [allTraces]);

  // STEP 2: Extract the current (most recent) plan state
  const currentPlan = useMemo(() => {
    // No plans if agent hasn't used write_todos tool
    if (planTraces.length === 0) return null;

    // Get the latest plan trace (plans are chronological, so last = latest)
    const latestPlan = planTraces[planTraces.length - 1];

    // Extract todos array from the trace content
    // Trace content structure: {todos: [{task: string, status: string}, ...]}
    const todos = latestPlan.content?.todos || [];

    return {
      todos,
      version: planTraces.length,  // Track how many times plan was updated
    };
  }, [planTraces]);

  // Check if execution has filesystem operations
  const hasFilesystemOps = useMemo(() => {
    return allTraces.some((t) => t.event_type === 'filesystem_operation');
  }, [allTraces]);

  // === AUTO-SCROLL TO LATEST TRACE ===
  // Automatically scrolls trace viewer to the bottom when new traces arrive.
  //
  // UX Pattern: Chat/log viewer behavior
  //   - User sees latest activity without manual scrolling
  //   - Smooth animation prevents jarring jumps
  //   - Trigger: Any time allTraces array changes (new WebSocket trace)
  //
  // Implementation:
  //   - tracesEndRef: invisible div at the end of trace list
  //   - scrollIntoView: browser API to bring element into viewport
  //   - behavior: 'smooth' for animated scroll (vs. 'auto' for instant)
  // === END PATTERN ===
  useEffect(() => {
    // Only scroll if we have traces and the end marker ref exists
    if (tracesEndRef.current && allTraces.length > 0) {
      tracesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [allTraces]);  // Re-run whenever trace list changes

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  const handleCancel = async () => {
    try {
      await cancelExecution.mutateAsync(executionId);
    } catch (error) {
      console.error('Failed to cancel execution:', error);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <Loading text="Loading execution details..." />
        </div>
      </div>
    );
  }

  if (isError || !execution) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <h2 className="text-xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700">Failed to load execution details.</p>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const isRunning = execution.status === 'running';
  const isFailed = execution.status === 'failed';
  const isCompleted = execution.status === 'completed';

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div
        ref={modalRef}
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b-gray-200">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-gray-900">
                Execution #{execution.id}
              </h2>
              <span
                className={`px-3 py-1 text-sm font-medium rounded-full ${
                  STATUS_COLORS[execution.status]
                }`}
              >
                {execution.status}
              </span>
              {isConnected && (
                <div className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                  <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
                  Live
                </div>
              )}
            </div>
            <div className="mt-2 text-sm text-gray-600 space-x-4">
              <span>
                <span className="font-medium">Agent:</span>{' '}
                {execution.agent_name || `Agent ${execution.agent_id}`}
              </span>
              <span>
                <span className="font-medium">Duration:</span>{' '}
                {formatDuration(execution.duration_seconds)}
              </span>
              <span>
                <span className="font-medium">Started:</span>{' '}
                {formatRelativeTime(execution.started_at)}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isRunning && (
              <button
                onClick={handleCancel}
                disabled={cancelExecution.isPending}
                className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700 disabled:opacity-50"
                aria-label="Cancel execution"
              >
                {cancelExecution.isPending ? 'Cancelling...' : 'Cancel'}
              </button>
            )}
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
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Input Section */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Input Prompt:</h3>
            <div className="bg-gray-50 border-gray-200 rounded p-4">
              <p className="text-sm text-gray-900 whitespace-pre-wrap">
                {execution.input_text}
              </p>
            </div>
          </div>

          {/* Plan Section - Show if agent has created a plan */}
          {currentPlan && currentPlan.todos.length > 0 && (
            <div>
              <PlanViewer plan={currentPlan} />
            </div>
          )}

          {/* Filesystem Viewer - Show if agent used filesystem tools */}
          {hasFilesystemOps && (
            <div>
              <FilesystemViewer traces={allTraces} />
            </div>
          )}

          {/* Traces Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700">
                Execution Trace {isConnected && '(Live)'}
              </h3>
              {wsError && (
                <div className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                  {wsError}
                </div>
              )}
            </div>
            <div className="bg-gray-50 border-gray-200 rounded p-4 space-y-2">
              {allTraces.length > 0 ? (
                <>
                  {allTraces.map((trace, index) => (
                    <TraceItem key={trace.sequence_number} trace={trace} index={index} />
                  ))}
                  <div ref={tracesEndRef} />
                </>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">
                  No traces available yet...
                </p>
              )}
            </div>
          </div>

          {/* Output Section (for completed executions) */}
          {isCompleted && execution.output_text && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Final Output:</h3>
              <div className="bg-gray-50 border border-gray-200 rounded p-4">
                <p className="text-sm text-gray-900 whitespace-pre-wrap">
                  {execution.output_text}
                </p>
              </div>
              <div className="mt-3 flex gap-4 text-sm text-gray-600">
                {execution.tokens_used !== null && (
                  <div key="tokens">
                    <span className="font-medium">Tokens Used:</span>{' '}
                    {formatNumber(execution.tokens_used)}
                  </div>
                )}
                {execution.tokens_used !== null && (
                  <div key="cost">
                    <span className="font-medium">Estimated Cost:</span> $
                    {((execution.tokens_used / 1000) * 0.01).toFixed(4)}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error Section (for failed executions) */}
          {isFailed && execution.error_message && (
            <div>
              <h3 className="text-sm font-medium text-red-700 mb-2">⚠️ Error</h3>
              <div className="bg-red-50 border border-red-200 rounded p-4">
                <p className="text-sm text-red-900">{execution.error_message}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExecutionDetailsModal;
