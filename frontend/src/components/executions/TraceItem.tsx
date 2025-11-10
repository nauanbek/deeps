import React, { useState } from 'react';
import { format } from 'date-fns';
import type { ExecutionTrace, TraceEventType } from '../../types/execution';
import { TRACE_EVENT_COLORS } from '../../utils/constants';

interface TraceItemProps {
  trace: ExecutionTrace;
  index: number;
}

const TRACE_TYPE_LABELS: Record<TraceEventType, string> = {
  llm_call: 'LLM Call',
  llm_response: 'LLM Response',
  tool_call: 'Tool Call',
  tool_result: 'Tool Result',
  error: 'Error',
  plan_update: 'Plan Update',
  filesystem_operation: 'Filesystem Operation',
  completion: 'Completion',
  agent_start: 'Agent Start',
  agent_end: 'Agent End',
};

const formatTimestamp = (timestamp: string): string => {
  try {
    return format(new Date(timestamp), 'HH:mm:ss');
  } catch {
    return timestamp;
  }
};

const formatJSON = (data: any): string => {
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
};

const truncateText = (text: string, maxLength: number = 200): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

const getFilesystemActionLabel = (tool: string): string => {
  const labels: Record<string, string> = {
    read_file: 'Read file',
    write_file: 'Write file',
    edit_file: 'Edit file',
    list_directory: 'List directory',
    create_directory: 'Create directory',
    delete_file: 'Delete file',
  };
  return labels[tool] || tool;
};

export const TraceItem: React.FC<TraceItemProps> = ({ trace, index }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const renderTraceContent = () => {
    const { event_type, content } = trace;

    switch (event_type) {
      case 'llm_call':
        return (
          <div className="space-y-2">
            {content.model && (
              <div>
                <span className="font-medium">Model:</span> {content.model}
              </div>
            )}
            {content.temperature !== undefined && (
              <div>
                <span className="font-medium">Temperature:</span> {content.temperature}
              </div>
            )}
            {content.max_tokens && (
              <div>
                <span className="font-medium">Max Tokens:</span> {content.max_tokens}
              </div>
            )}
            {content.messages && (
              <div>
                <span className="font-medium">Messages:</span>
                <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                  {formatJSON(content.messages)}
                </pre>
              </div>
            )}
          </div>
        );

      case 'llm_response':
        return (
          <div className="space-y-2">
            {content.content && (
              <div>
                <span className="font-medium">Response:</span>
                <div className="mt-1 text-sm bg-gray-50 p-2 rounded whitespace-pre-wrap">
                  {truncateText(content.content, 500)}
                </div>
              </div>
            )}
            {content.tokens !== undefined && (
              <div>
                <span className="font-medium">Tokens:</span> {content.tokens}
              </div>
            )}
          </div>
        );

      case 'tool_call':
        return (
          <div className="space-y-2">
            {content.tool && (
              <div>
                <span className="font-medium">Tool:</span> {content.tool}
              </div>
            )}
            {content.input && (
              <div>
                <span className="font-medium">Input:</span>
                <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                  {formatJSON(content.input)}
                </pre>
              </div>
            )}
          </div>
        );

      case 'tool_result':
        return (
          <div className="space-y-2">
            {content.result !== undefined && (
              <div>
                <span className="font-medium">Result:</span>
                <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                  {formatJSON(content.result)}
                </pre>
              </div>
            )}
            {content.success !== undefined && (
              <div>
                <span className="font-medium">Success:</span>{' '}
                {content.success ? '✓' : '✗'}
              </div>
            )}
          </div>
        );

      case 'error':
        return (
          <div className="space-y-2">
            {content.message && (
              <div className="text-red-600">
                <span className="font-medium">Message:</span> {content.message}
              </div>
            )}
            {content.error_type && (
              <div>
                <span className="font-medium">Type:</span> {content.error_type}
              </div>
            )}
            {content.stack && (
              <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                {content.stack}
              </pre>
            )}
          </div>
        );

      case 'plan_update':
        return (
          <div className="space-y-2">
            <div className="text-sm font-medium text-primary-700">
              Agent updated the plan
              {content.todos && ` (${content.todos.length} todos)`}
            </div>
            {content.todos && Array.isArray(content.todos) && content.todos.length > 0 && (
              <div className="mt-2 space-y-1">
                {content.todos.map((todo: any, idx: number) => (
                  <div key={idx} className="text-xs text-gray-700 flex items-start gap-2">
                    <span className="font-medium text-gray-500">{idx + 1}.</span>
                    <div className="flex-1">
                      <span>{todo.description}</span>
                      {todo.status && (
                        <span
                          className={`ml-2 text-xs font-medium uppercase ${
                            todo.status === 'completed'
                              ? 'text-green-600'
                              : todo.status === 'in_progress'
                              ? 'text-blue-600'
                              : todo.status === 'blocked'
                              ? 'text-red-600'
                              : 'text-gray-500'
                          }`}
                        >
                          [{todo.status}]
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {/* Legacy format support - plan array of strings */}
            {content.plan && Array.isArray(content.plan) && !content.todos && (
              <div>
                <span className="font-medium">Plan:</span>
                <ul className="mt-1 list-disc list-inside space-y-1">
                  {content.plan.map((item: string, idx: number) => (
                    <li key={idx} className="text-sm">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      case 'filesystem_operation':
        return (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-purple-700">
                {getFilesystemActionLabel(content.tool)}
              </span>
            </div>

            {/* File path */}
            {content.input?.path && (
              <div className="text-xs text-gray-700">
                <span className="font-mono bg-gray-100 px-2 py-1 rounded">
                  {content.input.path}
                </span>
              </div>
            )}

            {/* Content preview for write/edit */}
            {(content.tool === 'write_file' || content.tool === 'edit_file') &&
              content.input?.content && (
                <div className="mt-2">
                  <span className="font-medium text-xs">Content:</span>
                  <pre className="text-xs bg-gray-50 p-2 rounded border max-h-32 overflow-y-auto mt-1">
                    {truncateText(content.input.content, 200)}
                  </pre>
                </div>
              )}

            {/* Directory listing */}
            {content.tool === 'list_directory' && content.output?.files && (
              <div className="mt-2">
                <span className="font-medium text-xs">Files:</span>
                <ul className="text-xs text-gray-700 space-y-1 mt-1">
                  {content.output.files.slice(0, 10).map((file: string, idx: number) => (
                    <li key={idx} className="font-mono">
                      {file}
                    </li>
                  ))}
                  {content.output.files.length > 10 && (
                    <li className="text-gray-500">
                      ... and {content.output.files.length - 10} more
                    </li>
                  )}
                </ul>
              </div>
            )}

            {/* Success indicator */}
            {content.output?.success !== undefined && (
              <div className="text-xs">
                <span className="font-medium">Status:</span>{' '}
                <span className={content.output.success ? 'text-green-600' : 'text-red-600'}>
                  {content.output.success ? 'Success' : 'Failed'}
                </span>
              </div>
            )}
          </div>
        );

      case 'completion':
        return (
          <div className="space-y-2">
            {content.status && (
              <div>
                <span className="font-medium">Status:</span> {content.status}
              </div>
            )}
            {content.total_tokens !== undefined && (
              <div>
                <span className="font-medium">Total Tokens:</span> {content.total_tokens}
              </div>
            )}
          </div>
        );

      case 'agent_start':
      case 'agent_end':
        return (
          <div className="space-y-2">
            {content.agent_name && (
              <div>
                <span className="font-medium">Agent:</span> {content.agent_name}
              </div>
            )}
            {Object.keys(content).length > 0 && (
              <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                {formatJSON(content)}
              </pre>
            )}
          </div>
        );

      default:
        return (
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
            {formatJSON(content)}
          </pre>
        );
    }
  };

  return (
    <div className="border-l-4 border-gray-200 pl-4 py-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded"
        aria-expanded={isExpanded}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 text-xs text-gray-500 font-mono">
            [{trace.sequence_number}]
          </div>
          <div className="flex-shrink-0 text-xs text-gray-500 font-mono">
            {formatTimestamp(trace.timestamp)}
          </div>
          <div className="flex-1">
            <span
              className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                TRACE_EVENT_COLORS[trace.event_type]
              }`}
            >
              {TRACE_TYPE_LABELS[trace.event_type]}
            </span>
          </div>
          <div className="flex-shrink-0">
            <svg
              className={`w-5 h-5 text-gray-400 transform transition-transform ${
                isExpanded ? 'rotate-90' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="mt-3 ml-24 text-sm text-gray-700">
          {renderTraceContent()}
        </div>
      )}
    </div>
  );
};
