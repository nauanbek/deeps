/**
 * React Query hooks for Template API
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTemplates,
  getTemplate,
  getCategories,
  getFeaturedTemplates,
  getPopularTemplates,
  createAgentFromTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  importTemplate,
  exportTemplate,
} from '../api/templates';
import {
  TemplateFilters,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  CreateAgentFromTemplateRequest,
} from '../types/template';

/**
 * Hook to fetch list of templates with filters
 */
export const useTemplates = (filters: TemplateFilters = {}) => {
  return useQuery({
    queryKey: ['templates', filters],
    queryFn: () => getTemplates(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to fetch a single template by ID
 */
export const useTemplate = (id: number | null) => {
  return useQuery({
    queryKey: ['template', id],
    queryFn: () => getTemplate(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Hook to fetch available categories
 */
export const useCategories = () => {
  return useQuery({
    queryKey: ['template-categories'],
    queryFn: getCategories,
    staleTime: 30 * 60 * 1000, // 30 minutes - categories rarely change
  });
};

/**
 * Hook to fetch featured templates
 */
export const useFeaturedTemplates = () => {
  return useQuery({
    queryKey: ['templates', 'featured'],
    queryFn: getFeaturedTemplates,
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Hook to fetch popular templates
 */
export const usePopularTemplates = () => {
  return useQuery({
    queryKey: ['templates', 'popular'],
    queryFn: getPopularTemplates,
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Hook to create an agent from a template
 */
export const useCreateAgentFromTemplate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      data,
    }: {
      templateId: number;
      data: CreateAgentFromTemplateRequest;
    }) => createAgentFromTemplate(templateId, data),
    onSuccess: (agent, variables) => {
      // Invalidate agents list to show new agent
      queryClient.invalidateQueries({ queryKey: ['agents'] });

      // Update template use count
      queryClient.invalidateQueries({
        queryKey: ['template', variables.templateId],
      });
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};

/**
 * Hook to create a new template
 */
export const useCreateTemplate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTemplateRequest) => createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};

/**
 * Hook to update a template
 */
export const useUpdateTemplate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTemplateRequest }) =>
      updateTemplate(id, data),
    onSuccess: (updatedTemplate) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      queryClient.invalidateQueries({
        queryKey: ['template', updatedTemplate.id],
      });
    },
  });
};

/**
 * Hook to delete a template
 */
export const useDeleteTemplate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};

/**
 * Hook to import a template from JSON file
 */
export const useImportTemplate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => importTemplate(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};

/**
 * Hook to export a template as JSON
 */
export const useExportTemplate = () => {
  return useMutation({
    mutationFn: async (id: number) => {
      const blob = await exportTemplate(id);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `template-${id}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
};
