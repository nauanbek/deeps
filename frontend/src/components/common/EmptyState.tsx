import React from 'react';
import clsx from 'clsx';
import {
  FolderIcon,
  DocumentIcon,
  CubeIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  InboxIcon,
  CloudIcon,
} from '@heroicons/react/24/outline';

export type EmptyStateVariant =
  | 'default'
  | 'search'
  | 'folder'
  | 'document'
  | 'error'
  | 'inbox'
  | 'cloud';

interface EmptyStateProps {
  variant?: EmptyStateVariant;
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  secondaryAction?: React.ReactNode;
  compact?: boolean;
  className?: string;
}

const defaultIcons: Record<EmptyStateVariant, React.FC<{ className?: string }>> = {
  default: CubeIcon,
  search: MagnifyingGlassIcon,
  folder: FolderIcon,
  document: DocumentIcon,
  error: ExclamationTriangleIcon,
  inbox: InboxIcon,
  cloud: CloudIcon,
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  variant = 'default',
  icon,
  title,
  description,
  action,
  secondaryAction,
  compact = false,
  className,
}) => {
  const IconComponent = defaultIcons[variant];

  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center text-center',
        compact ? 'py-8 px-4' : 'py-16 px-6',
        className
      )}
    >
      {/* Icon */}
      <div
        className={clsx(
          'flex items-center justify-center rounded-full mb-4',
          compact
            ? 'w-12 h-12 bg-surface-100'
            : 'w-16 h-16 bg-gradient-to-br from-surface-100 to-surface-200'
        )}
      >
        {icon || (
          <IconComponent
            className={clsx(
              'text-surface-400',
              compact ? 'w-6 h-6' : 'w-8 h-8'
            )}
          />
        )}
      </div>

      {/* Title */}
      <h3
        className={clsx(
          'font-semibold text-surface-900',
          compact ? 'text-base mb-1' : 'text-lg mb-2'
        )}
      >
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p
          className={clsx(
            'text-surface-500 max-w-sm',
            compact ? 'text-sm mb-4' : 'text-base mb-6'
          )}
        >
          {description}
        </p>
      )}

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className={clsx('flex items-center gap-3', !description && 'mt-4')}>
          {action}
          {secondaryAction}
        </div>
      )}
    </div>
  );
};

// Search Empty State
interface SearchEmptyStateProps {
  query: string;
  onClear?: () => void;
  suggestions?: string[];
}

export const SearchEmptyState: React.FC<SearchEmptyStateProps> = ({
  query,
  onClear,
  suggestions,
}) => {
  return (
    <EmptyState
      variant="search"
      title={`No results for "${query}"`}
      description="Try adjusting your search or filter to find what you're looking for."
      action={
        onClear && (
          <button
            onClick={onClear}
            className="btn-secondary btn-sm"
          >
            Clear search
          </button>
        )
      }
      secondaryAction={
        suggestions && suggestions.length > 0 && (
          <div className="text-sm text-surface-500">
            Try: {suggestions.map((s, i) => (
              <span key={s}>
                <button className="text-primary-600 hover:underline">{s}</button>
                {i < suggestions.length - 1 && ', '}
              </span>
            ))}
          </div>
        )
      }
    />
  );
};

// Error Empty State
interface ErrorEmptyStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export const ErrorEmptyState: React.FC<ErrorEmptyStateProps> = ({
  title = 'Something went wrong',
  description = 'An error occurred while loading the data. Please try again.',
  onRetry,
}) => {
  return (
    <EmptyState
      variant="error"
      title={title}
      description={description}
      action={
        onRetry && (
          <button onClick={onRetry} className="btn-primary btn-sm">
            Try again
          </button>
        )
      }
    />
  );
};

export default EmptyState;
