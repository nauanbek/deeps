import React, { useRef, useEffect } from 'react';
import clsx from 'clsx';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface SearchInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  size?: 'sm' | 'md' | 'lg';
  clearable?: boolean;
  loading?: boolean;
  autoFocus?: boolean;
  shortcut?: string;
  onClear?: () => void;
  className?: string;
  containerClassName?: string;
}

const sizeStyles = {
  sm: {
    container: 'h-9',
    input: 'pl-9 pr-8 py-1.5 text-sm',
    icon: 'w-4 h-4 left-3',
    clear: 'right-2 p-1',
  },
  md: {
    container: 'h-11',
    input: 'pl-10 pr-9 py-2.5 text-sm',
    icon: 'w-5 h-5 left-3',
    clear: 'right-2.5 p-1',
  },
  lg: {
    container: 'h-12',
    input: 'pl-12 pr-10 py-3 text-base',
    icon: 'w-5 h-5 left-4',
    clear: 'right-3 p-1.5',
  },
};

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder = 'Search...',
  size = 'md',
  clearable = true,
  loading = false,
  autoFocus = false,
  shortcut,
  onClear,
  className,
  containerClassName,
  ...props
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const styles = sizeStyles[size];

  // Keyboard shortcut support
  useEffect(() => {
    if (!shortcut) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Handle Cmd/Ctrl + K or /
      if (
        (shortcut === 'k' && (e.metaKey || e.ctrlKey) && e.key === 'k') ||
        (shortcut === '/' && e.key === '/' && !e.metaKey && !e.ctrlKey)
      ) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      // Handle Escape
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        inputRef.current?.blur();
        if (value && onClear) {
          onClear();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcut, value, onClear]);

  const handleClear = () => {
    onChange('');
    onClear?.();
    inputRef.current?.focus();
  };

  return (
    <div className={clsx('relative', styles.container, containerClassName)}>
      {/* Search Icon or Loading Spinner */}
      <div
        className={clsx(
          'absolute top-1/2 -translate-y-1/2 text-surface-400 pointer-events-none',
          styles.icon
        )}
      >
        {loading ? (
          <svg
            className="animate-spin"
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
        ) : (
          <MagnifyingGlassIcon className="w-full h-full" />
        )}
      </div>

      {/* Input */}
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={clsx(
          'w-full h-full bg-white border border-surface-200 rounded-xl',
          'text-surface-900 placeholder:text-surface-400',
          'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
          'transition-all duration-200',
          styles.input,
          className
        )}
        {...props}
      />

      {/* Clear Button and Shortcut */}
      <div
        className={clsx(
          'absolute top-1/2 -translate-y-1/2 flex items-center gap-1',
          styles.clear
        )}
      >
        {/* Shortcut hint */}
        {shortcut && !value && (
          <kbd className="hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 text-xs font-medium text-surface-400 bg-surface-100 rounded border border-surface-200">
            {shortcut === 'k' ? (
              <>
                <span className="text-[10px]">⌘</span>K
              </>
            ) : (
              shortcut
            )}
          </kbd>
        )}

        {/* Clear button */}
        {clearable && value && (
          <button
            type="button"
            onClick={handleClear}
            className={clsx(
              'flex items-center justify-center rounded-lg',
              'text-surface-400 hover:text-surface-600 hover:bg-surface-100',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
              'transition-colors'
            )}
            aria-label="Clear search"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

// Filter Bar Component (Search + Filters)
interface FilterOption {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface FilterBarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  filters?: FilterOption[];
  activeFilter?: string;
  onFilterChange?: (filterId: string) => void;
  action?: React.ReactNode;
  className?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  searchValue,
  onSearchChange,
  searchPlaceholder = 'Search...',
  filters,
  activeFilter,
  onFilterChange,
  action,
  className,
}) => {
  return (
    <div
      className={clsx(
        'flex flex-col sm:flex-row items-stretch sm:items-center gap-4',
        className
      )}
    >
      {/* Search */}
      <div className="flex-1 min-w-0">
        <SearchInput
          value={searchValue}
          onChange={onSearchChange}
          placeholder={searchPlaceholder}
          shortcut="/"
        />
      </div>

      {/* Filters */}
      {filters && filters.length > 0 && onFilterChange && (
        <div className="flex gap-1 p-1 bg-surface-100 rounded-xl">
          {filters.map((filter) => (
            <button
              key={filter.id}
              onClick={() => onFilterChange(filter.id)}
              className={clsx(
                'flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg',
                'transition-all duration-200',
                activeFilter === filter.id
                  ? 'bg-white text-surface-900 shadow-sm'
                  : 'text-surface-600 hover:text-surface-900'
              )}
            >
              {filter.icon}
              {filter.label}
            </button>
          ))}
        </div>
      )}

      {/* Action */}
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
};

export default SearchInput;
