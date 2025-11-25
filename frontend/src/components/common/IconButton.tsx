import React from 'react';
import clsx from 'clsx';

export type IconButtonVariant = 'default' | 'primary' | 'danger' | 'success' | 'ghost';
export type IconButtonSize = 'xs' | 'sm' | 'md' | 'lg';

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  variant?: IconButtonVariant;
  size?: IconButtonSize;
  label: string; // Required for accessibility
  isLoading?: boolean;
  badge?: number | string;
  tooltip?: string;
}

const variantStyles: Record<IconButtonVariant, string> = {
  default:
    'bg-white text-surface-600 border border-surface-200 hover:bg-surface-50 hover:text-surface-900 hover:border-surface-300 focus-visible:ring-surface-400',
  primary:
    'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500 shadow-sm hover:shadow-md',
  danger:
    'bg-white text-error-600 border border-surface-200 hover:bg-error-50 hover:border-error-200 focus-visible:ring-error-500',
  success:
    'bg-white text-success-600 border border-surface-200 hover:bg-success-50 hover:border-success-200 focus-visible:ring-success-500',
  ghost:
    'text-surface-500 hover:bg-surface-100 hover:text-surface-700 focus-visible:ring-surface-400',
};

const sizeStyles: Record<IconButtonSize, { button: string; icon: string }> = {
  xs: { button: 'w-7 h-7', icon: 'w-3.5 h-3.5' },
  sm: { button: 'w-8 h-8', icon: 'w-4 h-4' },
  md: { button: 'w-10 h-10', icon: 'w-5 h-5' },
  lg: { button: 'w-12 h-12', icon: 'w-6 h-6' },
};

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  variant = 'default',
  size = 'md',
  label,
  isLoading = false,
  badge,
  tooltip,
  className,
  disabled,
  ...props
}) => {
  const sizeConfig = sizeStyles[size];

  return (
    <button
      type="button"
      className={clsx(
        'relative inline-flex items-center justify-center rounded-xl transition-all duration-200',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
        'active:scale-95',
        variantStyles[variant],
        sizeConfig.button,
        className
      )}
      disabled={disabled || isLoading}
      aria-label={label}
      title={tooltip || label}
      {...props}
    >
      {isLoading ? (
        <svg
          className={clsx('animate-spin', sizeConfig.icon)}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
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
        <span className={clsx('flex items-center justify-center', sizeConfig.icon)}>
          {icon}
        </span>
      )}
      {badge !== undefined && (
        <span
          className={clsx(
            'absolute -top-1 -right-1 flex items-center justify-center',
            'min-w-[18px] h-[18px] px-1 text-xs font-bold',
            'bg-error-500 text-white rounded-full',
            'ring-2 ring-white'
          )}
        >
          {typeof badge === 'number' && badge > 99 ? '99+' : badge}
        </span>
      )}
      <span className="sr-only">{label}</span>
    </button>
  );
};

// Icon Button Group
interface IconButtonGroupProps {
  children: React.ReactNode;
  className?: string;
}

export const IconButtonGroup: React.FC<IconButtonGroupProps> = ({
  children,
  className,
}) => {
  return (
    <div
      className={clsx(
        'inline-flex items-center rounded-xl border border-surface-200 overflow-hidden',
        className
      )}
    >
      {React.Children.map(children, (child, index) => {
        if (!React.isValidElement(child)) return child;

        return React.cloneElement(child, {
          className: clsx(
            child.props.className,
            'rounded-none border-0',
            index > 0 && 'border-l border-surface-200'
          ),
        } as React.HTMLAttributes<HTMLElement>);
      })}
    </div>
  );
};

export default IconButton;
