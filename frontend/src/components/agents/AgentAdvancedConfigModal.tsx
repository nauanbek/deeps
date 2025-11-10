/**
 * Agent Advanced Configuration Modal
 *
 * Modal with tabs for advanced agent configuration:
 * - Backend storage
 * - Long-term memory
 * - HITL approvals
 */

import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useToast } from '../../hooks/useToast';
import BackendConfigTab from './advanced/BackendConfigTab';
import MemorySetupTab from './advanced/MemorySetupTab';
import HITLConfigTab from './advanced/HITLConfigTab';
import type { Agent } from '../../types/agent';

interface AgentAdvancedConfigModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'backend' | 'memory' | 'hitl';

const TABS: Array<{ id: TabType; label: string; description: string }> = [
  {
    id: 'backend',
    label: 'Backend Storage',
    description: 'Configure storage backend (State, Filesystem, Store, Composite)',
  },
  {
    id: 'memory',
    label: 'Long-term Memory',
    description: 'Manage persistent memory across sessions',
  },
  {
    id: 'hitl',
    label: 'HITL Approvals',
    description: 'Configure human-in-the-loop approval workflows',
  },
];

export const AgentAdvancedConfigModal: React.FC<AgentAdvancedConfigModalProps> = ({
  agent,
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('backend');
  const { success, error } = useToast();

  const handleSuccess = () => {
    success('Configuration saved successfully');
  };

  const handleError = (message: string) => {
    error(message);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Advanced Configuration: ${agent.name}`}
      size="xl"
    >
      <div className="space-y-6">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                  ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
                aria-current={activeTab === tab.id ? 'page' : undefined}
              >
                <div className="flex flex-col items-start">
                  <span>{tab.label}</span>
                  <span className="text-xs font-normal text-gray-400 mt-1">
                    {tab.description}
                  </span>
                </div>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[500px]">
          {activeTab === 'backend' && (
            <BackendConfigTab
              agentId={agent.id}
              onSuccess={handleSuccess}
              onError={handleError}
            />
          )}
          {activeTab === 'memory' && (
            <MemorySetupTab
              agentId={agent.id}
              onSuccess={handleSuccess}
              onError={handleError}
            />
          )}
          {activeTab === 'hitl' && (
            <HITLConfigTab
              agentId={agent.id}
              onSuccess={handleSuccess}
              onError={handleError}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default AgentAdvancedConfigModal;
