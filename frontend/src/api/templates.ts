/**
 * Template API Client
 *
 * Provides HTTP methods for managing agent templates including:
 * - Browsing template library with filters (category, public/private, featured)
 * - Creating agents from pre-configured templates
 * - Creating custom templates from existing agents
 * - Importing/exporting templates as JSON for sharing
 * - Managing template visibility and featuring
 *
 * Templates enable rapid agent creation from proven configurations.
 * All methods require authentication via JWT token.
 *
 * @module api/templates
 */

import { apiClient } from './client';
import {
  Template,
  TemplateFilters,
  TemplateListResponse,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  CreateAgentFromTemplateRequest,
  TemplateCategory,
} from '../types/template';
import { Agent } from '../types/agent';

/**
 * Fetch templates with optional filters.
 *
 * Returns paginated list of templates matching the provided filters.
 * Useful for building template libraries, marketplaces, and galleries.
 *
 * @param {TemplateFilters} [filters={}] - Optional filters
 * @param {string} [filters.category] - Filter by category
 * @param {boolean} [filters.is_public] - Filter by public/private visibility
 * @param {boolean} [filters.is_featured] - Filter by featured status
 * @param {string} [filters.search] - Search by name/description
 * @param {number} [filters.created_by_id] - Filter by creator user ID
 * @param {number} [filters.skip] - Pagination offset
 * @param {number} [filters.limit] - Pagination limit
 * @returns {Promise<TemplateListResponse>} Paginated template list
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * // Get all featured templates
 * const featured = await getTemplates({ is_featured: true });
 *
 * @example
 * // Search templates by keyword
 * const searchResults = await getTemplates({ search: 'research' });
 */
export const getTemplates = async (
  filters: TemplateFilters = {}
): Promise<TemplateListResponse> => {
  const params = new URLSearchParams();

  if (filters.category) params.append('category', filters.category);
  if (filters.is_public !== undefined)
    params.append('is_public', String(filters.is_public));
  if (filters.is_featured !== undefined)
    params.append('is_featured', String(filters.is_featured));
  if (filters.search) params.append('search', filters.search);
  if (filters.created_by_id)
    params.append('created_by_id', String(filters.created_by_id));
  if (filters.skip !== undefined) params.append('skip', String(filters.skip));
  if (filters.limit !== undefined) params.append('limit', String(filters.limit));

  const response = await apiClient.get<{
    templates: Template[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  }>(`/templates/?${params}`);

  // Extract templates from wrapped response
  const items = response.data.templates;
  return {
    items,
    total: response.data.total,
    skip: filters.skip || 0,
    limit: filters.limit || 100,
  };
};

/**
 * Fetch a single template by ID.
 *
 * Returns complete template details including configuration,
 * metadata, and usage statistics.
 *
 * @param {number} id - Template ID to retrieve
 * @returns {Promise<Template>} Template details
 * @throws {AxiosError} 404 if template not found, 401 if not authenticated
 *
 * @example
 * const template = await getTemplate(123);
 * console.log(template.name, template.category);
 */
export const getTemplate = async (id: number): Promise<Template> => {
  const response = await apiClient.get<Template>(`/templates/${id}`);
  return response.data;
};

/**
 * Fetch all available template categories.
 *
 * Returns list of categories with counts for organizing template library.
 * Categories include: research, code_review, data_analysis, etc.
 *
 * @returns {Promise<TemplateCategory[]>} Available template categories
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * const categories = await getCategories();
 * categories.forEach(c => console.log(`${c.name}: ${c.count} templates`));
 */
export const getCategories = async (): Promise<TemplateCategory[]> => {
  const response = await apiClient.get<TemplateCategory[]>('/templates/categories');
  return response.data;
};

/**
 * Fetch featured templates.
 *
 * Returns curated templates highlighted by administrators.
 * Featured templates are high-quality, well-tested configurations
 * ideal for new users.
 *
 * @returns {Promise<Template[]>} Featured template list
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * const featured = await getFeaturedTemplates();
 */
export const getFeaturedTemplates = async (): Promise<Template[]> => {
  const response = await apiClient.get<Template[]>('/templates/featured');
  return response.data;
};

/**
 * Fetch popular templates sorted by usage count.
 *
 * Returns templates ranked by number of times they've been used
 * to create agents. Useful for discovering community favorites.
 *
 * @returns {Promise<Template[]>} Popular template list sorted by usage descending
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * const popular = await getPopularTemplates();
 * console.log(`Most popular: ${popular[0].name} (${popular[0].use_count} uses)`);
 */
export const getPopularTemplates = async (): Promise<Template[]> => {
  const response = await apiClient.get<Template[]>('/templates/popular');
  return response.data;
};

/**
 * Create a new agent from a template.
 *
 * Instantiates an agent using the template's configuration as a base.
 * You can override specific fields like name, model, or temperature.
 * Increments template's use_count.
 *
 * @param {number} templateId - Template ID to use
 * @param {CreateAgentFromTemplateRequest} data - Agent customization data
 * @param {string} data.name - Agent name (required)
 * @param {string} [data.model_name] - Override model
 * @param {number} [data.temperature] - Override temperature
 * @returns {Promise<Agent>} Created agent
 * @throws {AxiosError} 404 if template not found, 400 if validation fails
 *
 * @example
 * const agent = await createAgentFromTemplate(123, {
 *   name: 'My Research Assistant'
 * });
 */
export const createAgentFromTemplate = async (
  templateId: number,
  data: CreateAgentFromTemplateRequest
): Promise<Agent> => {
  const response = await apiClient.post<Agent>(
    `/templates/${templateId}/create-agent`,
    data
  );
  return response.data;
};

/**
 * Create a new template.
 *
 * Creates a template configuration that can be used to instantiate agents.
 * Can be public (shared with all users) or private (personal only).
 *
 * @param {CreateTemplateRequest} data - Template configuration
 * @returns {Promise<Template>} Created template with generated ID
 * @throws {AxiosError} 400 if validation fails, 401 if not authenticated
 *
 * @example
 * const template = await createTemplate({
 *   name: 'Custom Research Template',
 *   category: 'research',
 *   description: 'Specialized template for academic research',
 *   model_provider: 'anthropic',
 *   model_name: 'claude-3-5-sonnet-20241022',
 *   system_prompt: 'You are an academic research assistant...',
 *   is_public: false
 * });
 */
export const createTemplate = async (
  data: CreateTemplateRequest
): Promise<Template> => {
  const response = await apiClient.post<Template>('/templates/', data);
  return response.data;
};

/**
 * Update an existing template.
 *
 * Modifies template configuration. Only the template creator
 * or administrators can update templates.
 *
 * @param {number} id - Template ID to update
 * @param {UpdateTemplateRequest} data - Partial template data to update
 * @returns {Promise<Template>} Updated template
 * @throws {AxiosError} 404 if not found, 403 if not owner, 401 if not authenticated
 *
 * @example
 * const updated = await updateTemplate(123, {
 *   description: 'Updated description',
 *   is_featured: true
 * });
 */
export const updateTemplate = async (
  id: number,
  data: UpdateTemplateRequest
): Promise<Template> => {
  const response = await apiClient.put<Template>(`/templates/${id}`, data);
  return response.data;
};

/**
 * Delete a template (soft delete).
 *
 * Marks template as inactive but preserves it in database.
 * Only the template creator or administrators can delete templates.
 *
 * @param {number} id - Template ID to delete
 * @returns {Promise<void>}
 * @throws {AxiosError} 404 if not found, 403 if not owner, 401 if not authenticated
 *
 * @example
 * await deleteTemplate(123);
 * console.log('Template deleted');
 */
export const deleteTemplate = async (id: number): Promise<void> => {
  await apiClient.delete(`/templates/${id}`);
};

/**
 * Import a template from JSON file.
 *
 * Uploads and validates a template JSON file exported from another
 * DeepAgents instance. Useful for sharing templates across environments.
 *
 * @param {File} file - JSON file containing template configuration
 * @returns {Promise<Template>} Imported template
 * @throws {AxiosError} 400 if JSON invalid, 401 if not authenticated
 *
 * @example
 * const fileInput = document.querySelector('input[type="file"]');
 * const file = fileInput.files[0];
 * const imported = await importTemplate(file);
 * console.log('Template imported:', imported.name);
 */
export const importTemplate = async (file: File): Promise<Template> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<Template>('/templates/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Export a template as JSON file.
 *
 * Downloads template configuration as a JSON blob that can be
 * shared with other users or imported into other DeepAgents instances.
 *
 * @param {number} id - Template ID to export
 * @returns {Promise<Blob>} JSON blob containing template data
 * @throws {AxiosError} 404 if template not found, 401 if not authenticated
 *
 * @example
 * const blob = await exportTemplate(123);
 * const url = URL.createObjectURL(blob);
 * const a = document.createElement('a');
 * a.href = url;
 * a.download = 'template.json';
 * a.click();
 */
export const exportTemplate = async (id: number): Promise<Blob> => {
  const response = await apiClient.get(`/templates/${id}/export`, {
    responseType: 'blob',
  });
  return response.data;
};
