/**
 * Memory Setup Tab
 * Manages long-term memory namespace and files
 */

import React, { useState } from 'react';
import { Button } from '../../common/Button';
import { TrashIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import {
  useMemoryNamespace,
  useCreateMemoryNamespace,
  useDeleteMemoryNamespace,
  useMemoryFiles,
  useCreateMemoryFile,
  useDeleteMemoryFile,
} from '../../../hooks/useAdvancedConfig';

interface MemorySetupTabProps {
  agentId: number;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const MemorySetupTab: React.FC<MemorySetupTabProps> = ({
  agentId,
  onSuccess,
  onError,
}) => {
  const { data: namespace, isLoading: nsLoading } = useMemoryNamespace(agentId);
  const { data: files, isLoading: filesLoading } = useMemoryFiles(agentId, undefined, !!namespace);

  const createNs = useCreateMemoryNamespace();
  const deleteNs = useDeleteMemoryNamespace();
  const createFile = useCreateMemoryFile();
  const deleteFile = useDeleteMemoryFile();

  const [newFileName, setNewFileName] = useState('');
  const [newFileContent, setNewFileContent] = useState('');

  const handleCreateNamespace = async () => {
    try {
      await createNs.mutateAsync({ agentId });
      onSuccess?.();
    } catch (err: unknown) {
      let errorMessage = 'Failed to create namespace';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      onError?.(errorMessage);
    }
  };

  const handleDeleteNamespace = async () => {
    if (window.confirm('Delete memory namespace and all files?')) {
      try {
        await deleteNs.mutateAsync(agentId);
        onSuccess?.();
      } catch (err: unknown) {
        let errorMessage = 'Failed to delete namespace';
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosError = err as { response?: { data?: { detail?: string } } };
          errorMessage = axiosError.response?.data?.detail || errorMessage;
        }
        onError?.(errorMessage);
      }
    }
  };

  const handleCreateFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFileName) return;

    try {
      await createFile.mutateAsync({
        agentId,
        data: { key: newFileName, value: newFileContent }
      });
      setNewFileName('');
      setNewFileContent('');
      onSuccess?.();
    } catch (err: unknown) {
      let errorMessage = 'Failed to create file';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      onError?.(errorMessage);
    }
  };

  const handleDeleteFile = async (fileKey: string) => {
    if (window.confirm(`Delete file "${fileKey}"?`)) {
      try {
        await deleteFile.mutateAsync({ agentId, fileKey });
        onSuccess?.();
      } catch (err: unknown) {
        let errorMessage = 'Failed to delete file';
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosError = err as { response?: { data?: { detail?: string } } };
          errorMessage = axiosError.response?.data?.detail || errorMessage;
        }
        onError?.(errorMessage);
      }
    }
  };

  if (nsLoading) {
    return <div className="py-12 text-center text-gray-600">Loading...</div>;
  }

  if (!namespace) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Long-term Memory</h3>
          <p className="mt-1 text-sm text-gray-600">
            Enable persistent memory across agent sessions using /memories/ path.
          </p>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <p className="text-sm text-blue-800">
            No memory namespace configured. Create one to enable long-term memory for this agent.
          </p>
        </div>
        <Button variant="primary" onClick={handleCreateNamespace} disabled={createNs.isPending}>
          {createNs.isPending ? 'Creating...' : 'Create Memory Namespace'}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Long-term Memory</h3>
        <p className="mt-1 text-sm text-gray-600">
          Namespace: <code className="bg-gray-100 px-2 py-1 rounded">{namespace.namespace}</code>
        </p>
      </div>

      {/* Create file form */}
      <form onSubmit={handleCreateFile} className="space-y-4 bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900">Create Memory File</h4>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">File Name</label>
          <input
            type="text"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            placeholder="e.g., context.md"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
          <textarea
            value={newFileContent}
            onChange={(e) => setNewFileContent(e.target.value)}
            placeholder="File content..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          />
        </div>
        <Button type="submit" variant="primary" size="sm" disabled={createFile.isPending}>
          {createFile.isPending ? 'Creating...' : 'Create File'}
        </Button>
      </form>

      {/* Files list */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Memory Files ({files?.total_files || 0})</h4>
        {filesLoading ? (
          <div className="text-sm text-gray-600">Loading files...</div>
        ) : files && files.files.length > 0 ? (
          <div className="space-y-2">
            {files.files.map((file) => (
              <div key={file.key} className="flex items-center justify-between bg-white border border-gray-200 rounded-md p-3">
                <div className="flex items-center space-x-3">
                  <DocumentTextIcon className="w-5 h-5 text-gray-400" />
                  <div>
                    <div className="text-sm font-medium text-gray-900">{file.key}</div>
                    <div className="text-xs text-gray-500">{file.size_bytes} bytes</div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteFile(file.key)}
                  disabled={deleteFile.isPending}
                >
                  <TrashIcon className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-600 bg-gray-50 p-4 rounded-md">No files yet</div>
        )}
      </div>

      {/* Delete namespace */}
      <div className="pt-4 border-t border-gray-200">
        <Button variant="danger" onClick={handleDeleteNamespace} disabled={deleteNs.isPending}>
          {deleteNs.isPending ? 'Deleting...' : 'Delete Namespace & All Files'}
        </Button>
      </div>
    </div>
  );
};

export default MemorySetupTab;
