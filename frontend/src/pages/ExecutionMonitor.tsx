import React, { useState, useEffect, Suspense, lazy } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, CardHeader } from '../components/common/Card';
import { ExecutionTable } from '../components/executions/ExecutionTable';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import { useExecutions, useCancelExecution } from '../hooks/useExecutions';
import type { ExecutionStatus } from '../types/execution';

// Lazy load modal (only shown on user interaction)
const ExecutionDetailsModal = lazy(() => import('../components/executions/ExecutionDetailsModal').then(m => ({ default: m.ExecutionDetailsModal })));

export const ExecutionMonitor: React.FC = () => {
  const location = useLocation();
  const [statusFilter, setStatusFilter] = useState<ExecutionStatus | 'all'>('all');
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(null);

  const cancelExecution = useCancelExecution();

  // Fetch executions with optional status filter
  const { data: executions, isLoading, refetch } = useExecutions({
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

  // === AUTO-REFRESH POLLING FOR RUNNING EXECUTIONS ===
  // Implements adaptive polling: only refresh when there are active executions.
  //
  // Problem: We need near-real-time updates for execution status, but:
  //   - WebSocket: Complex, requires connection management
  //   - Always polling: Wastes bandwidth when no active executions
  //
  // Solution: Conditional polling that activates only when needed
  //
  // Polling lifecycle:
  //   1. Check if any executions have status='running'
  //   2. If yes: Start 5-second interval polling
  //   3. If no: Stop interval (cleanup function)
  //   4. Re-evaluate when executions array changes
  //
  // Example timeline:
  //   T=0s: User loads page, no running executions → No polling
  //   T=10s: User starts execution → hasRunningExecutions=true → Start polling
  //   T=15s, 20s, 25s: Refetch every 5 seconds
  //   T=30s: Execution completes → hasRunningExecutions=false → Stop polling
  //
  // Benefits:
  //   - Reduced server load (only poll when necessary)
  //   - Battery friendly (no unnecessary background work)
  //   - Still provides responsive UI for active executions
  // === END POLLING PATTERN ===
  useEffect(() => {
    // Check if ANY execution in the list has status='running'
    // Array.some() returns true if at least one element matches the condition
    const hasRunningExecutions = executions?.some(
      (exec) => exec.status === 'running'
    );

    // Only start polling if there are running executions
    if (hasRunningExecutions) {
      // Set up interval to refetch every 5000ms (5 seconds)
      const interval = setInterval(() => {
        refetch();  // TanStack Query refetch function
      }, 5000);

      // Cleanup function: Clear interval when effect re-runs or component unmounts
      // This prevents memory leaks from abandoned intervals
      return () => clearInterval(interval);
    }
    // If no running executions, don't set up interval (implicitly return undefined)
  }, [executions, refetch]);  // Re-run when executions data or refetch function changes

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

  return (
    <PageErrorBoundary>
      <main className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Execution Monitor</h1>
          <p className="text-gray-600 mt-2">
            Track and monitor agent executions in real-time
          </p>
        </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div>
          <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Filter by Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ExecutionStatus | 'all')}
            className="px-3 py-2 border-gray-300 rounded-md shadow-sm focus-visible:ring-primary-500 focus-visible:border-primary-500"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <div className="ml-auto">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Executions Table */}
      <Card>
        <CardHeader
          title="Executions"
          subtitle={`${executions?.length || 0} executions`}
        />
        <ExecutionTable
          executions={executions || []}
          onViewDetails={handleViewDetails}
          onCancel={handleCancel}
          isLoading={isLoading}
        />
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
      </main>
    </PageErrorBoundary>
  );
};

export default ExecutionMonitor;
