/**
 * TemplateLibrary Component
 * Main component for browsing and searching templates
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useTemplates, useFeaturedTemplates } from '../../hooks/useTemplates';
import { Template, TemplateCategory } from '../../types/template';
import { TemplateCard, TemplateCardSkeleton } from './TemplateCard';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  PlusIcon,
  ArrowUpTrayIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';

interface TemplateLibraryProps {
  onUseTemplate: (template: Template) => void;
  onViewDetails: (template: Template) => void;
  onImportTemplate?: () => void;
  currentUserId?: number;
}

const ITEMS_PER_PAGE = 12;

export const TemplateLibrary: React.FC<TemplateLibraryProps> = ({
  onUseTemplate,
  onViewDetails,
  onImportTemplate,
  currentUserId,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<
    TemplateCategory | 'all'
  >('all');
  const [showMyTemplates, setShowMyTemplates] = useState(false);
  const [showFeaturedOnly, setShowFeaturedOnly] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(0); // Reset to first page on search
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Build filters
  const filters = {
    search: debouncedSearch || undefined,
    category: selectedCategory !== 'all' ? selectedCategory : undefined,
    created_by_id: showMyTemplates && currentUserId ? currentUserId : undefined,
    is_featured: showFeaturedOnly || undefined,
    skip: currentPage * ITEMS_PER_PAGE,
    limit: ITEMS_PER_PAGE,
  };

  const { data: templatesData, isLoading, error } = useTemplates(filters);
  const { data: featuredTemplates } = useFeaturedTemplates();

  const templates = templatesData?.items || [];
  const totalTemplates = templatesData?.total || 0;
  const totalPages = Math.ceil(totalTemplates / ITEMS_PER_PAGE);

  const handleCategoryChange = useCallback((category: TemplateCategory | 'all') => {
    setSelectedCategory(category);
    setCurrentPage(0);
  }, []);

  const handleMyTemplatesToggle = useCallback(() => {
    setShowMyTemplates(!showMyTemplates);
    setCurrentPage(0);
  }, [showMyTemplates]);

  const handleFeaturedToggle = useCallback(() => {
    setShowFeaturedOnly(!showFeaturedOnly);
    setCurrentPage(0);
  }, [showFeaturedOnly]);

  const categories: Array<{ value: TemplateCategory | 'all'; label: string }> = [
    { value: 'all', label: 'All Categories' },
    { value: 'research', label: 'Research' },
    { value: 'coding', label: 'Coding' },
    { value: 'customer_support', label: 'Customer Support' },
    { value: 'data_analysis', label: 'Data Analysis' },
    { value: 'content_writing', label: 'Content Writing' },
    { value: 'code_review', label: 'Code Review' },
    { value: 'documentation', label: 'Documentation' },
    { value: 'testing', label: 'Testing' },
    { value: 'general', label: 'General' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Template Library</h1>
          <p className="mt-2 text-gray-600">
            Browse and use pre-configured agent templates
          </p>
        </div>
        {onImportTemplate && (
          <button
            onClick={onImportTemplate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700 shadow-sm"
          >
            <ArrowUpTrayIcon className="w-5 h-5" />
            Import Template
          </button>
        )}
      </div>

      {/* Featured Templates Carousel */}
      {featuredTemplates && featuredTemplates.length > 0 && !showMyTemplates && (
        <div className="bg-gradient-to-r from-primary-500 to-purple-600 rounded-xl p-6 text-white">
          <h2 className="text-xl font-bold mb-4">Featured Templates</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredTemplates.slice(0, 3).map((template) => (
              <div
                key={template.id}
                className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-4 cursor-pointer hover:bg-opacity-20 transition-all"
                onClick={() => onViewDetails(template)}
              >
                <h3 className="font-semibold mb-2">{template.name}</h3>
                <p className="text-sm text-white text-opacity-90 line-clamp-2">
                  {template.description}
                </p>
                <div className="mt-3 flex items-center justify-between text-sm">
                  <span>{template.use_count} uses</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onUseTemplate(template);
                    }}
                    className="px-3 py-1 bg-white text-primary-600 rounded hover:bg-opacity-90 transition-colors font-medium"
                  >
                    Use Template
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search templates..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-transparent"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div className="relative">
            <FunnelIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            <select
              value={selectedCategory}
              onChange={(e) =>
                handleCategoryChange(e.target.value as TemplateCategory | 'all')
              }
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-transparent appearance-none bg-white cursor-pointer min-w-[200px]"
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* Toggle Filters */}
          <div className="flex gap-2">
            <button
              onClick={handleFeaturedToggle}
              className={`px-4 py-2 rounded-lg transition-colors ${
                showFeaturedOnly
                  ? 'bg-primary-100 border border-primary-300 text-primary-700'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Featured
            </button>
            {currentUserId && (
              <button
                onClick={handleMyTemplatesToggle}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  showMyTemplates
                    ? 'bg-primary-100 border border-primary-300 text-primary-700'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                My Templates
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Results Count */}
      {!isLoading && (
        <div className="text-sm text-gray-600">
          {totalTemplates === 0
            ? 'No templates found'
            : `Showing ${currentPage * ITEMS_PER_PAGE + 1}-${Math.min(
                (currentPage + 1) * ITEMS_PER_PAGE,
                totalTemplates
              )} of ${totalTemplates} templates`}
        </div>
      )}

      {/* Templates Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, index) => (
            <TemplateCardSkeleton key={index} />
          ))}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700">
            Error loading templates. Please try again later.
          </p>
        </div>
      ) : templates.length === 0 ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <PlusIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No templates found
          </h3>
          <p className="text-gray-600 mb-4">
            {debouncedSearch
              ? 'Try adjusting your search or filters'
              : 'Start by browsing featured templates or importing your own'}
          </p>
          {debouncedSearch && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory('all');
                setShowFeaturedOnly(false);
                setShowMyTemplates(false);
              }}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {templates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onUseTemplate={onUseTemplate}
                onViewDetails={onViewDetails}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
                aria-label="Previous page"
              >
                <ChevronLeftIcon className="w-5 h-5" />
              </button>

              <div className="flex gap-1">
                {Array.from({ length: totalPages }).map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentPage(index)}
                    className={`px-3 py-1 rounded-lg transition-colors ${
                      currentPage === index
                        ? 'bg-primary-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>

              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={currentPage === totalPages - 1}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
                aria-label="Next page"
              >
                <ChevronRightIcon className="w-5 h-5" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
