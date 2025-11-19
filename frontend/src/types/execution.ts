export interface Execution {
  id: number;
  agent_id: number;
  agent_name?: string;
  input_text: string;
  output_text: string | null;
  status: ExecutionStatus;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  tokens_used: number | null;
  error_message: string | null;
}

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface ExecutionCreate {
  agent_id: number;
  input_text: string;
}

export type TraceEventType =
  | 'llm_call'
  | 'llm_response'
  | 'tool_call'
  | 'tool_result'
  | 'error'
  | 'plan_update'
  | 'filesystem_operation'
  | 'completion'
  | 'agent_start'
  | 'agent_end';

export interface ExecutionTrace {
  id?: number;
  execution_id: number;
  sequence_number: number;
  event_type: TraceEventType;
  content: Record<string, any>;
  timestamp: string;
  created_at?: string;
}

export interface StreamChunk {
  type: 'token' | 'trace' | 'error' | 'complete';
  data: unknown;
}
