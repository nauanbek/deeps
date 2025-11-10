/**
 * TypeScript types for Agent Templates
 */

export interface Template {
  id: number;
  name: string;
  description: string;
  category: TemplateCategory;
  tags: string[];
  config_template: ConfigTemplate;
  is_public: boolean;
  is_featured: boolean;
  use_count: number;
  created_by_id: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export type TemplateCategory =
  | 'research'
  | 'coding'
  | 'customer_support'
  | 'data_analysis'
  | 'content_writing'
  | 'code_review'
  | 'documentation'
  | 'testing'
  | 'general';

export interface ConfigTemplate {
  model_provider: 'anthropic' | 'openai';
  model_name: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  planning_enabled: boolean;
  filesystem_enabled: boolean;
  tool_ids: number[];
  additional_config?: Record<string, any>;
}

export interface CreateAgentFromTemplateRequest {
  template_id: number;
  name: string;
  description?: string;
  config_overrides?: Record<string, any>;
}

export interface CreateTemplateRequest {
  name: string;
  description: string;
  category: TemplateCategory;
  tags: string[];
  config_template: ConfigTemplate;
  is_public?: boolean;
  is_featured?: boolean;
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  category?: TemplateCategory;
  tags?: string[];
  config_template?: ConfigTemplate;
  is_public?: boolean;
  is_featured?: boolean;
}

export interface TemplateFilters {
  category?: TemplateCategory;
  is_public?: boolean;
  is_featured?: boolean;
  search?: string;
  created_by_id?: number;
  skip?: number;
  limit?: number;
}

export interface TemplateListResponse {
  items: Template[];
  total: number;
  skip: number;
  limit: number;
}

// Category metadata for UI
export interface CategoryInfo {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: string;
}

export const CATEGORY_INFO: Record<TemplateCategory, CategoryInfo> = {
  research: {
    label: 'Research',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-300',
    icon: '🔬',
  },
  coding: {
    label: 'Coding',
    color: 'text-purple-700',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-300',
    icon: '💻',
  },
  customer_support: {
    label: 'Customer Support',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-300',
    icon: '💬',
  },
  data_analysis: {
    label: 'Data Analysis',
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-300',
    icon: '📊',
  },
  content_writing: {
    label: 'Content Writing',
    color: 'text-pink-700',
    bgColor: 'bg-pink-100',
    borderColor: 'border-pink-300',
    icon: '✍️',
  },
  code_review: {
    label: 'Code Review',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-300',
    icon: '🔍',
  },
  documentation: {
    label: 'Documentation',
    color: 'text-primary-700',
    bgColor: 'bg-primary-100',
    borderColor: 'border-primary-300',
    icon: '📚',
  },
  testing: {
    label: 'Testing',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-300',
    icon: '🧪',
  },
  general: {
    label: 'General',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-300',
    icon: '⚙️',
  },
};
