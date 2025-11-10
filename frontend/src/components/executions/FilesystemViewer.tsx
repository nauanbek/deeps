import React, { useMemo, useState } from 'react';
import { DocumentIcon, FolderIcon } from '@heroicons/react/24/outline';
import type { ExecutionTrace } from '../../types/execution';

interface FilesystemNode {
  path: string;
  type: 'file' | 'directory';
  content?: string;
  size?: number;
  updated_at?: string;
}

interface FilesystemViewerProps {
  traces: ExecutionTrace[];
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const FilesystemViewer: React.FC<FilesystemViewerProps> = ({ traces }) => {
  const [selectedFile, setSelectedFile] = useState<FilesystemNode | null>(null);

  // Build filesystem state from traces
  const filesystem = useMemo(() => {
    const files: Map<string, FilesystemNode> = new Map();

    traces
      .filter((t) => t.event_type === 'filesystem_operation')
      .forEach((trace) => {
        const { tool, input, output } = trace.content;

        switch (tool) {
          case 'write_file':
          case 'edit_file':
            if (input?.path) {
              files.set(input.path, {
                path: input.path,
                type: 'file',
                content: input.content,
                size: input.content?.length || 0,
                updated_at: trace.timestamp,
              });
            }
            break;

          case 'create_directory':
            if (input?.path) {
              files.set(input.path, {
                path: input.path,
                type: 'directory',
                updated_at: trace.timestamp,
              });
            }
            break;

          case 'delete_file':
            if (input?.path) {
              files.delete(input.path);
            }
            break;

          // read_file and list_directory don't modify filesystem state
          default:
            break;
        }
      });

    return Array.from(files.values()).sort((a, b) => a.path.localeCompare(b.path));
  }, [traces]);

  if (filesystem.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
        <FolderIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
        <p className="text-gray-600">No filesystem operations yet</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="border-b border-gray-200 px-4 py-3 bg-gray-50">
        <h4 className="font-semibold text-gray-900">Virtual Filesystem</h4>
        <p className="text-xs text-gray-600 mt-1">
          {filesystem.length} item{filesystem.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-gray-200">
        {/* File List */}
        <div className="p-4 max-h-96 overflow-y-auto">
          <ul className="space-y-2">
            {filesystem.map((node) => (
              <li
                key={node.path}
                className={`flex items-center space-x-2 p-2 rounded cursor-pointer hover:bg-gray-50 ${
                  selectedFile?.path === node.path
                    ? 'bg-primary-50 border border-primary-200'
                    : ''
                }`}
                onClick={() => setSelectedFile(node)}
              >
                {node.type === 'directory' ? (
                  <FolderIcon className="w-4 h-4 text-yellow-600 flex-shrink-0" />
                ) : (
                  <DocumentIcon className="w-4 h-4 text-blue-600 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-mono truncate">{node.path}</p>
                  {node.size !== undefined && (
                    <p className="text-xs text-gray-500">{formatBytes(node.size)}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* File Content Preview */}
        <div className="p-4 max-h-96 overflow-y-auto bg-gray-50">
          {selectedFile ? (
            <div>
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-900">{selectedFile.path}</p>
                <p className="text-xs text-gray-500">
                  {selectedFile.type === 'file' ? 'File' : 'Directory'}
                </p>
              </div>

              {selectedFile.type === 'file' && selectedFile.content && (
                <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto">
                  {selectedFile.content}
                </pre>
              )}

              {selectedFile.type === 'directory' && (
                <p className="text-sm text-gray-600 italic">Directory</p>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <DocumentIcon className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">Select a file to view its contents</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilesystemViewer;
