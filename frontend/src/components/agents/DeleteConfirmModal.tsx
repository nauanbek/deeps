import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { Modal, ModalFooter } from '../common/Modal';
import { Button } from '../common/Button';
import type { Agent } from '../../types/agent';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  agent: Agent | null;
  isDeleting?: boolean;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  agent,
  isDeleting = false,
}) => {
  if (!agent) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Agent"
      size="sm"
      showCloseButton={!isDeleting}
    >
      <div className="space-y-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon
              className="h-10 w-10 text-red-600"
              aria-hidden="true"
            />
          </div>
          <div className="flex-1">
            <p className="text-sm text-gray-700">
              Are you sure you want to delete{' '}
              <span className="font-semibold text-gray-900">{agent.name}</span>?
            </p>
            <p className="mt-2 text-sm text-gray-600">
              This action cannot be undone. All agent configurations, execution
              history, and associated data will be permanently removed.
            </p>
          </div>
        </div>
      </div>

      <ModalFooter>
        <Button
          variant="secondary"
          onClick={onClose}
          disabled={isDeleting}
        >
          Cancel
        </Button>
        <Button
          variant="danger"
          onClick={onConfirm}
          isLoading={isDeleting}
          disabled={isDeleting}
        >
          {isDeleting ? 'Deleting...' : 'Delete Agent'}
        </Button>
      </ModalFooter>
    </Modal>
  );
};

export default DeleteConfirmModal;
