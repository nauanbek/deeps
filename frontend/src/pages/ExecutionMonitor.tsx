import React, { useState, useEffect, Suspense, lazy } from 'react';
import { useLocation } from 'react-router-dom';
import clsx from 'clsx';
import {
  ArrowPathIcon,
  FunnelIcon,
  PlayCircleIcon,
} from '@heroicons/react/24/outline';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Select } from '../components/common/Select';
import { PageLayout, PageHeader } from '../components/common/PageLayout';
import { EmptyState } from '../components/common/EmptyState';
import { ExecutionTable } from '../components/executions/ExecutionTable';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import { useExecutions, useCancelExecution } from '../hooks/useExecutions';
import type { ExecutionStatus } from '../types/execution';

// Lazy load modal (only shown on user interaction)
const ExecutionDetailsModal = lazy(() => import('../components/executions/ExecutionDetailsModal').then(m => ({ default: m.ExecutionDetailsModal })));

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

export const ExecutionMonitor: React.FC = () => {
  const location = useLocation();
  const [statusFilter, setStatusFilter] = useState<ExecutionStatus | 'all'>('all');
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(null);

  const cancelExecution = useCancelExecution();

  // Fetch executions with optional status filter
  const { data: executions, isLoading, refetch, isFetching } = useExecutions({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    limit: 100,
  });

  // Auto-open details modal from URL query param
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const executionId = params.get('execution');
    if (executionId) {
      setSelectedExecutionId(Number(executionId));
    }
  }, [location.search]);

  // Auto-refresh polling for running executions
  useEffect(() => {
    const hasRunningExecutions = executions?.some(
      (exec) => exec.status === 'running'
    );

    if (hasRunningExecutions) {
      const interval = setInterval(() => {
        refetch();
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [executions, refetch]);

  const handleViewDetails = (id: number) => {
    setSelectedExecutionId(id);
  };

  const handleCancel = async (id: number) => {
    try {
      await cancelExecution.mutateAsync(id);
    } catch (error) {
      console.error('Failed to cancel execution:', error);
    }
  };

  const handleCloseModal = () => {
    setSelectedExecutionId(null);
    // Clear query param from URL
    const params = new URLSearchParams(location.search);
    params.delete('execution');
    window.history.replaceState({}, '', `${location.pathname}?${params}`);
  };

  // Count running executions for status indicator
  const runningCount = executions?.filter(e => e.status === 'running').length || 0;

  return (
    <PageErrorBoundary>
      <PageLayout>
        {/* Header */}
        <PageHeader
          title="Execution Monitor"
          subtitle="Track and monitor agent executions in real-time"
          action={
            <div className="flex items-center gap-3">
              {runningCount > 0 && (
                <Badge variant="success" className="animate-pulse">
                  {runningCount} running
                </Badge>
              )}
              <Button
                variant="secondary"
                size="md"
                onClick={() => refetch()}
                isLoading={isFetching}
                leftIcon={<ArrowPathIcon className={clsx('w-4 h-4', isFetching && 'animate-spin')} />}
              >
                Refresh
              </Button>
            </div>
          }
        />

        {/* Filters */}
        <div className="mb-6">
          <Card className="p-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div className="flex items-center gap-2 text-surface-600">
                <FunnelIcon className="w-5 h-5" />
                <span className="text-sm font-medium">Filters</span>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as ExecutionStatus | 'all')}
                  options={statusOptions}
                  className="w-40"
                />
              </div>

              {statusFilter !== 'all' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setStatusFilter('all')}
                >
                  Clear filters
                </Button>
              )}

              <div className="sm:ml-auto text-sm text-surface-500">
                {executions?.length || 0} executions
              </div>
            </div>
          </Card>
        </div>

        {/* Executions Table */}
        <Card>
          <CardHeader
            title="Executions"
            subtitle="View execution history and live status"
          />
          {executions && executions.length === 0 && !isLoading ? (
            <div className="p-8">
              <EmptyState
                variant="default"
                icon={<PlayCircleIcon className="w-12 h-12" />}
                title="No executions yet"
                description={statusFilter !== 'all'
                  ? `No ${statusFilter} executions found`
                  : "Run an agent to see executions here"}
              />
            </div>
          ) : (
            <ExecutionTable
              executions={executions || []}
              onViewDetails={handleViewDetails}
              onCancel={handleCancel}
              isLoading={isLoading}
            />
          )}
        </Card>

        {/* Execution Details Modal with WebSocket */}
        {selectedExecutionId && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={handleCloseModal}>
              <ExecutionDetailsModal
                executionId={selectedExecutionId}
                onClose={handleCloseModal}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}
      </PageLayout>
    </PageErrorBoundary>
  );
};

export default ExecutionMonitor;
