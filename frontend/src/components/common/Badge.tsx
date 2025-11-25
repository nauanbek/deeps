import React from 'react';
import clsx from 'clsx';

export type BadgeVariant = 'primary' | 'success' | 'warning' | 'error' | 'neutral' | 'accent';
export type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  removable?: boolean;
  onRemove?: () => void;
  className?: string;
  icon?: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, string> = {
  primary: 'bg-primary-100 text-primary-700 border-primary-200',
  success: 'bg-success-100 text-success-700 border-success-200',
  warning: 'bg-warning-100 text-warning-700 border-warning-200',
  error: 'bg-error-100 text-error-700 border-error-200',
  neutral: 'bg-surface-100 text-surface-600 border-surface-200',
  accent: 'bg-accent-100 text-accent-700 border-accent-200',
};

const dotStyles: Record<BadgeVariant, string> = {
  primary: 'bg-primary-500',
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  error: 'bg-error-500',
  neutral: 'bg-surface-400',
  accent: 'bg-accent-500',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  removable = false,
  onRemove,
  className,
  icon,
}) => {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 font-medium rounded-full border transition-colors',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {dot && (
        <span
          className={clsx('w-1.5 h-1.5 rounded-full', dotStyles[variant])}
          aria-hidden="true"
        />
      )}
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
      {removable && (
        <button
          type="button"
          onClick={onRemove}
          className={clsx(
            'flex-shrink-0 ml-0.5 -mr-1 p-0.5 rounded-full',
            'hover:bg-black/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
            'transition-colors'
          )}
          aria-label="Remove"
        >
          <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor">
            <path d="M4.293 4.293a1 1 0 011.414 0L6 4.586l.293-.293a1 1 0 111.414 1.414L7.414 6l.293.293a1 1 0 01-1.414 1.414L6 7.414l-.293.293a1 1 0 01-1.414-1.414L4.586 6l-.293-.293a1 1 0 010-1.414z" />
          </svg>
        </button>
      )}
    </span>
  );
};

// Status Badge with built-in icons
interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'pending' | 'error' | 'success';
  label?: string;
  size?: BadgeSize;
}

const statusConfig = {
  active: { variant: 'success' as BadgeVariant, label: 'Active', dot: true },
  inactive: { variant: 'neutral' as BadgeVariant, label: 'Inactive', dot: true },
  pending: { variant: 'warning' as BadgeVariant, label: 'Pending', dot: true },
  error: { variant: 'error' as BadgeVariant, label: 'Error', dot: true },
  success: { variant: 'success' as BadgeVariant, label: 'Success', dot: true },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = 'md',
}) => {
  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size={size} dot={config.dot}>
      {label || config.label}
    </Badge>
  );
};

export default Badge;
