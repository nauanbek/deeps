// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

// Model Options
export const AVAILABLE_MODELS = [
  'gpt-4',
  'gpt-4-turbo-preview',
  'gpt-3.5-turbo',
  'claude-3-opus-20240229',
  'claude-3-sonnet-20240229',
  'claude-3-haiku-20240307',
] as const;

// Temperature Range
export const TEMPERATURE_MIN = 0.0;
export const TEMPERATURE_MAX = 2.0;
export const TEMPERATURE_DEFAULT = 0.7;

// Max Tokens Range
export const MAX_TOKENS_MIN = 100;
export const MAX_TOKENS_MAX = 8000;
export const MAX_TOKENS_DEFAULT = 2000;

// Execution Status Colors
export const STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-yellow-100 text-yellow-800',
} as const;

// Trace Event Type Colors
export const TRACE_EVENT_COLORS = {
  llm_call: 'bg-blue-100 text-blue-800',
  llm_response: 'bg-green-100 text-green-800',
  tool_call: 'bg-purple-100 text-purple-800',
  tool_result: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  plan_update: 'bg-primary-100 text-primary-800',
  filesystem_operation: 'bg-purple-100 text-purple-800 border-purple-200',
  completion: 'bg-green-100 text-green-800',
  agent_start: 'bg-cyan-100 text-cyan-800',
  agent_end: 'bg-cyan-100 text-cyan-800',
} as const;

// Refresh Intervals (milliseconds)
export const REFRESH_INTERVAL = {
  FAST: 2000,    // 2 seconds
  MEDIUM: 10000, // 10 seconds
  SLOW: 30000,   // 30 seconds
} as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];
