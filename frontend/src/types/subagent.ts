import { Agent } from './agent';

export interface Subagent {
  id: number;
  agent_id: number;
  subagent_id: number;
  delegation_prompt: string | null;
  priority: number;
  created_at: string;
  subagent: Agent;
}

export interface SubagentCreate {
  subagent_id: number;
  delegation_prompt?: string;
  priority?: number;
}

export interface SubagentUpdate {
  delegation_prompt?: string;
  priority?: number;
}
