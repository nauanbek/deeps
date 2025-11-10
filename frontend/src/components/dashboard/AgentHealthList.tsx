import React from 'react';
import { AgentHealthCard } from './AgentHealthCard';
import type { AgentHealth } from '../../types/monitoring';

export interface AgentHealthListProps {
  agents: AgentHealth[];
}

export const AgentHealthList: React.FC<AgentHealthListProps> = ({ agents }) => {
  if (agents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No agent health data available</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {agents.map((agent) => (
        <AgentHealthCard key={agent.agent_id} health={agent} />
      ))}
    </div>
  );
};

export default AgentHealthList;
