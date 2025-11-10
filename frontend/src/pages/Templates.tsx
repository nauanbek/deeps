/**
 * Templates Page
 * Full page for browsing and managing agent templates
 */

import React, { useState, Suspense, lazy } from 'react';
import { useNavigate } from 'react-router-dom';
import { TemplateLibrary } from '../components/templates/TemplateLibrary';
import { Template, CreateAgentFromTemplateRequest } from '../types/template';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import {
  useCreateAgentFromTemplate,
  useImportTemplate,
  useExportTemplate,
  useDeleteTemplate,
} from '../hooks/useTemplates';

// Lazy load modals (only shown on user interaction)
const TemplateDetailModal = lazy(() => import('../components/templates/TemplateDetailModal').then(m => ({ default: m.TemplateDetailModal })));
const CreateAgentFromTemplateModal = lazy(() => import('../components/templates/CreateAgentFromTemplateModal').then(m => ({ default: m.CreateAgentFromTemplateModal })));
const ImportTemplateModal = lazy(() => import('../components/templates/ImportTemplateModal').then(m => ({ default: m.ImportTemplateModal })));

export const Templates: React.FC = () => {
  const navigate = useNavigate();

  // Modal states
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isCreateAgentModalOpen, setIsCreateAgentModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // Mutations
  const createAgentMutation = useCreateAgentFromTemplate();
  const importTemplateMutation = useImportTemplate();
  const exportTemplateMutation = useExportTemplate();
  const deleteTemplateMutation = useDeleteTemplate();

  // Handlers
  const handleViewDetails = (template: Template) => {
    setSelectedTemplate(template);
    setIsDetailModalOpen(true);
  };

  const handleUseTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setIsDetailModalOpen(false);
    setIsCreateAgentModalOpen(true);
  };

  const handleCreateAgent = async (
    templateId: number,
    data: CreateAgentFromTemplateRequest
  ) => {
    try {
      const agent = await createAgentMutation.mutateAsync({
        templateId,
        data,
      });

      // Close modal
      setIsCreateAgentModalOpen(false);
      setSelectedTemplate(null);

      // Navigate to agent details
      navigate(`/agents/${agent.id}`);
    } catch (error) {
      console.error('Error creating agent:', error);
    }
  };

  const handleImportTemplate = async (file: File) => {
    try {
      await importTemplateMutation.mutateAsync(file);

      // Close modal
      setIsImportModalOpen(false);
    } catch (error) {
      console.error('Error importing template:', error);
    }
  };

  const handleExportTemplate = async (templateId: number) => {
    try {
      await exportTemplateMutation.mutateAsync(templateId);
    } catch (error) {
      console.error('Error exporting template:', error);
    }
  };

  const handleDeleteTemplate = async (template: Template) => {
    if (
      window.confirm(
        `Are you sure you want to delete the template "${template.name}"? This action cannot be undone.`
      )
    ) {
      try {
        await deleteTemplateMutation.mutateAsync(template.id);

        // Close modal
        setIsDetailModalOpen(false);
        setSelectedTemplate(null);
      } catch (error) {
        console.error('Error deleting template:', error);
      }
    }
  };

  const handleEditTemplate = (template: Template) => {
    // TODO: Implement edit functionality
    alert('Edit functionality coming soon!');
  };

  return (
    <PageErrorBoundary>
      <main className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TemplateLibrary
          onUseTemplate={handleUseTemplate}
          onViewDetails={handleViewDetails}
          onImportTemplate={() => setIsImportModalOpen(true)}
          currentUserId={1} // Note: Integrate with auth context for multi-user support
        />

          {/* Template Detail Modal */}
          {isDetailModalOpen && selectedTemplate && (
            <Suspense fallback={null}>
              <ModalErrorBoundary
                onClose={() => {
                  setIsDetailModalOpen(false);
                  setSelectedTemplate(null);
                }}
              >
                <TemplateDetailModal
                  template={selectedTemplate!}
                  isOpen={isDetailModalOpen}
                  onClose={() => {
                    setIsDetailModalOpen(false);
                    setSelectedTemplate(null);
                  }}
                  onUseTemplate={handleUseTemplate}
                  onEditTemplate={handleEditTemplate}
                  onDeleteTemplate={handleDeleteTemplate}
                  onExportTemplate={handleExportTemplate}
                  currentUserId={1} // TODO: Get from auth context
                />
              </ModalErrorBoundary>
            </Suspense>
          )}

          {/* Create Agent Modal */}
          {isCreateAgentModalOpen && (
            <Suspense fallback={null}>
              <ModalErrorBoundary
                onClose={() => {
                  setIsCreateAgentModalOpen(false);
                  setSelectedTemplate(null);
                }}
              >
                <CreateAgentFromTemplateModal
                  template={selectedTemplate}
                  isOpen={isCreateAgentModalOpen}
                  onClose={() => {
                    setIsCreateAgentModalOpen(false);
                    setSelectedTemplate(null);
                  }}
                  onSubmit={handleCreateAgent}
                  isLoading={createAgentMutation.isPending}
                />
              </ModalErrorBoundary>
            </Suspense>
          )}

          {/* Import Template Modal */}
          {isImportModalOpen && (
            <Suspense fallback={null}>
              <ModalErrorBoundary onClose={() => setIsImportModalOpen(false)}>
                <ImportTemplateModal
                  isOpen={isImportModalOpen}
                  onClose={() => setIsImportModalOpen(false)}
                  onImport={handleImportTemplate}
                  isLoading={importTemplateMutation.isPending}
                />
              </ModalErrorBoundary>
            </Suspense>
          )}
        </div>
      </main>
    </PageErrorBoundary>
  );
};

export default Templates;
