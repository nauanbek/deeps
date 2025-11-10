/**
 * React hooks for Advanced Configuration API
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { advancedConfigApi } from '../api/advancedConfig';
import type {
  BackendConfig,
  MemoryNamespace,
  MemoryFile,
  InterruptConfig,
  ApprovalDecision,
  AgentAdvancedConfig,
} from '../api/advancedConfig';

// ============================================================================
// Query Keys
// ============================================================================

export const advancedConfigKeys = {
  all: ['advancedConfig'] as const,
  backendConfig: (agentId: number) => [...advancedConfigKeys.all, 'backend', agentId] as const,
  memoryNamespace: (agentId: number) => [...advancedConfigKeys.all, 'memory', 'namespace', agentId] as const,
  memoryFiles: (agentId: number, prefix?: string) => [...advancedConfigKeys.all, 'memory', 'files', agentId, prefix] as const,
  interruptConfigs: (agentId: number) => [...advancedConfigKeys.all, 'interrupt', agentId] as const,
  executionApprovals: (executionId: number) => [...advancedConfigKeys.all, 'approvals', executionId] as const,
  allConfigs: (agentId: number) => [...advancedConfigKeys.all, 'combined', agentId] as const,
};

// ============================================================================
// Backend Configuration Hooks
// ============================================================================

export const useBackendConfig = (agentId: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: advancedConfigKeys.backendConfig(agentId),
    queryFn: () => advancedConfigApi.getBackendConfig(agentId),
    enabled,
    retry: false, // Don't retry on 404
  });
};

export const useCreateBackendConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: number; data: Omit<BackendConfig, 'id' | 'agent_id' | 'created_at' | 'updated_at'> }) =>
      advancedConfigApi.createBackendConfig(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.backendConfig(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(variables.agentId) });
    },
  });
};

export const useUpdateBackendConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: number; data: Partial<BackendConfig> }) =>
      advancedConfigApi.updateBackendConfig(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.backendConfig(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(variables.agentId) });
    },
  });
};

export const useDeleteBackendConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentId: number) => advancedConfigApi.deleteBackendConfig(agentId),
    onSuccess: (_, agentId) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.backendConfig(agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(agentId) });
    },
  });
};

// ============================================================================
// Memory Namespace Hooks
// ============================================================================

export const useMemoryNamespace = (agentId: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: advancedConfigKeys.memoryNamespace(agentId),
    queryFn: () => advancedConfigApi.getMemoryNamespace(agentId),
    enabled,
    retry: false,
  });
};

export const useCreateMemoryNamespace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, data = {} }: { agentId: number; data?: { store_type?: string; config?: Record<string, any> } }) =>
      advancedConfigApi.createMemoryNamespace(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.memoryNamespace(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(variables.agentId) });
    },
  });
};

export const useDeleteMemoryNamespace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentId: number) => advancedConfigApi.deleteMemoryNamespace(agentId),
    onSuccess: (_, agentId) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.memoryNamespace(agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.memoryFiles(agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(agentId) });
    },
  });
};

// ============================================================================
// Memory Files Hooks
// ============================================================================

export const useMemoryFiles = (agentId: number, prefix?: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: advancedConfigKeys.memoryFiles(agentId, prefix),
    queryFn: () => advancedConfigApi.listMemoryFiles(agentId, prefix),
    enabled,
    retry: false,
  });
};

export const useCreateMemoryFile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: number; data: { key: string; value: string; content_type?: string } }) =>
      advancedConfigApi.createMemoryFile(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.memoryFiles(variables.agentId) });
    },
  });
};

export const useDeleteMemoryFile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, fileKey }: { agentId: number; fileKey: string }) =>
      advancedConfigApi.deleteMemoryFile(agentId, fileKey),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.memoryFiles(variables.agentId) });
    },
  });
};

// ============================================================================
// HITL Interrupt Configuration Hooks
// ============================================================================

export const useInterruptConfigs = (agentId: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: advancedConfigKeys.interruptConfigs(agentId),
    queryFn: () => advancedConfigApi.listInterruptConfigs(agentId),
    enabled,
  });
};

export const useCreateInterruptConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: number; data: Omit<InterruptConfig, 'id' | 'agent_id' | 'created_at' | 'updated_at'> }) =>
      advancedConfigApi.createInterruptConfig(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.interruptConfigs(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(variables.agentId) });
    },
  });
};

export const useUpdateInterruptConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, toolName, data }: { agentId: number; toolName: string; data: Partial<InterruptConfig> }) =>
      advancedConfigApi.updateInterruptConfig(agentId, toolName, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.interruptConfigs(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(variables.agentId) });
    },
  });
};

export const useDeleteInterruptConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, toolName }: { agentId: number; toolName: string }) =>
      advancedConfigApi.deleteInterruptConfig(agentId, toolName),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.interruptConfigs(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.allConfigs(variables.agentId) });
    },
  });
};

// ============================================================================
// Execution Approvals Hooks
// ============================================================================

export const useExecutionApprovals = (executionId: number, statusFilter?: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: advancedConfigKeys.executionApprovals(executionId),
    queryFn: () => advancedConfigApi.listExecutionApprovals(executionId, statusFilter),
    enabled,
    refetchInterval: 5000, // Poll every 5 seconds for pending approvals
  });
};

export const useSubmitApprovalDecision = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ executionId, approvalId, decision }: { executionId: number; approvalId: number; decision: ApprovalDecision }) =>
      advancedConfigApi.submitApprovalDecision(executionId, approvalId, decision),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advancedConfigKeys.executionApprovals(variables.executionId) });
    },
  });
};

// ============================================================================
// Combined Hook
// ============================================================================

export const useAgentAdvancedConfig = (agentId: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: advancedConfigKeys.allConfigs(agentId),
    queryFn: () => advancedConfigApi.getAllAdvancedConfig(agentId),
    enabled,
  });
};
