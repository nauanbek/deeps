import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export type ModalSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: ModalSize;
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
  icon?: React.ReactNode;
  iconVariant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  className?: string;
}

const sizeClasses: Record<ModalSize, string> = {
  xs: 'max-w-xs',
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  full: 'max-w-5xl',
};

const iconVariantStyles = {
  default: 'bg-surface-100 text-surface-600',
  primary: 'bg-primary-100 text-primary-600',
  success: 'bg-success-100 text-success-600',
  warning: 'bg-warning-100 text-warning-600',
  error: 'bg-error-100 text-error-600',
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  icon,
  iconVariant = 'default',
  className,
}) => {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-50"
        onClose={closeOnOverlayClick ? onClose : () => {}}
      >
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-surface-900/60 backdrop-blur-sm" />
        </Transition.Child>

        {/* Modal container */}
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95 translate-y-4"
              enterTo="opacity-100 scale-100 translate-y-0"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100 translate-y-0"
              leaveTo="opacity-0 scale-95 translate-y-4"
            >
              <Dialog.Panel
                className={clsx(
                  'w-full transform overflow-hidden rounded-2xl bg-white shadow-2xl transition-all',
                  'max-h-[90vh] flex flex-col',
                  sizeClasses[size],
                  className
                )}
              >
                {/* Header */}
                {(title || showCloseButton || icon) && (
                  <div className="flex items-start gap-4 px-6 pt-6 pb-4">
                    {/* Icon */}
                    {icon && (
                      <div
                        className={clsx(
                          'flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center',
                          iconVariantStyles[iconVariant]
                        )}
                      >
                        {icon}
                      </div>
                    )}

                    {/* Title & Description */}
                    <div className="flex-1 min-w-0">
                      {title && (
                        <Dialog.Title
                          as="h3"
                          className="text-lg font-semibold text-surface-900"
                        >
                          {title}
                        </Dialog.Title>
                      )}
                      {description && (
                        <Dialog.Description className="mt-1 text-sm text-surface-500">
                          {description}
                        </Dialog.Description>
                      )}
                    </div>

                    {/* Close button */}
                    {showCloseButton && (
                      <button
                        type="button"
                        onClick={onClose}
                        className={clsx(
                          'flex-shrink-0 p-2 -mt-1 -mr-2 rounded-xl',
                          'text-surface-400 hover:text-surface-600 hover:bg-surface-100',
                          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                          'transition-colors'
                        )}
                        aria-label="Close modal"
                      >
                        <XMarkIcon className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                )}

                {/* Content */}
                <div className="flex-1 overflow-y-auto px-6 pb-6">
                  {children}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

// Modal Header Component (for custom headers)
interface ModalHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const ModalHeader: React.FC<ModalHeaderProps> = ({ children, className }) => {
  return (
    <div className={clsx('px-6 pt-6 pb-4', className)}>
      {children}
    </div>
  );
};

// Modal Body Component
interface ModalBodyProps {
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const ModalBody: React.FC<ModalBodyProps> = ({
  children,
  className,
  noPadding = false,
}) => {
  return (
    <div className={clsx(!noPadding && 'px-6 py-4', className)}>
      {children}
    </div>
  );
};

// Modal Footer Component
interface ModalFooterProps {
  children: React.ReactNode;
  className?: string;
  bordered?: boolean;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({
  children,
  className,
  bordered = true,
}) => {
  return (
    <div
      className={clsx(
        'flex items-center justify-end gap-3 px-6 py-4',
        bordered && 'border-t border-surface-100 bg-surface-50/50',
        className
      )}
    >
      {children}
    </div>
  );
};

// Confirmation Modal Component
interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'primary';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  isLoading = false,
  icon,
}) => {
  const variantConfig = {
    danger: {
      iconVariant: 'error' as const,
      buttonClass: 'btn-danger',
      defaultIcon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      ),
    },
    warning: {
      iconVariant: 'warning' as const,
      buttonClass: 'bg-gradient-to-r from-warning-500 to-warning-600 text-white hover:from-warning-600 hover:to-warning-700',
      defaultIcon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      ),
    },
    primary: {
      iconVariant: 'primary' as const,
      buttonClass: 'btn-primary',
      defaultIcon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
  };

  const config = variantConfig[variant];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="sm"
      icon={icon || config.defaultIcon}
      iconVariant={config.iconVariant}
      title={title}
      description={message}
      closeOnOverlayClick={!isLoading}
    >
      <ModalFooter bordered={false} className="pt-4">
        <button
          type="button"
          onClick={onClose}
          disabled={isLoading}
          className="btn-secondary btn-md"
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isLoading}
          className={clsx('btn btn-md', config.buttonClass)}
        >
          {isLoading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Processing...
            </>
          ) : (
            confirmLabel
          )}
        </button>
      </ModalFooter>
    </Modal>
  );
};

export default Modal;
