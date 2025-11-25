import React from 'react';
import clsx from 'clsx';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'success' | 'outline';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  children: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: clsx(
    'bg-gradient-to-r from-primary-600 to-primary-700 text-white',
    'hover:from-primary-700 hover:to-primary-800 hover:shadow-lg hover:shadow-primary-500/25',
    'focus-visible:ring-primary-500',
    'active:scale-[0.98]'
  ),
  secondary: clsx(
    'bg-white text-surface-700 border border-surface-200',
    'hover:bg-surface-50 hover:border-surface-300 hover:shadow-soft',
    'focus-visible:ring-surface-400',
    'active:scale-[0.98]'
  ),
  danger: clsx(
    'bg-gradient-to-r from-error-500 to-error-600 text-white',
    'hover:from-error-600 hover:to-error-700 hover:shadow-lg hover:shadow-error-500/25',
    'focus-visible:ring-error-500',
    'active:scale-[0.98]'
  ),
  success: clsx(
    'bg-gradient-to-r from-success-500 to-success-600 text-white',
    'hover:from-success-600 hover:to-success-700 hover:shadow-lg hover:shadow-success-500/25',
    'focus-visible:ring-success-500',
    'active:scale-[0.98]'
  ),
  ghost: clsx(
    'text-surface-600 bg-transparent',
    'hover:bg-surface-100 hover:text-surface-900',
    'focus-visible:ring-surface-400'
  ),
  outline: clsx(
    'bg-transparent text-primary-600 border border-primary-300',
    'hover:bg-primary-50 hover:border-primary-400',
    'focus-visible:ring-primary-500'
  ),
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: 'px-2.5 py-1 text-xs min-h-[32px] rounded-lg gap-1',
  sm: 'px-3 py-1.5 text-sm min-h-[36px] rounded-lg gap-1.5',
  md: 'px-4 py-2 text-sm min-h-[44px] rounded-xl gap-2',
  lg: 'px-6 py-3 text-base min-h-[52px] rounded-xl gap-2',
};

const iconSizeStyles: Record<ButtonSize, string> = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-4 h-4',
  lg: 'w-5 h-5',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  disabled,
  children,
  ...props
}) => {
  const baseStyles = clsx(
    'inline-flex items-center justify-center font-medium',
    'transition-all duration-200 ease-out',
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none'
  );

  return (
    <button
      className={clsx(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && 'w-full',
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg
          className={clsx('animate-spin', iconSizeStyles[size])}
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
        leftIcon && (
          <span className={clsx('flex-shrink-0', iconSizeStyles[size])}>
            {leftIcon}
          </span>
        )
      )}
      <span>{children}</span>
      {!isLoading && rightIcon && (
        <span className={clsx('flex-shrink-0', iconSizeStyles[size])}>
          {rightIcon}
        </span>
      )}
    </button>
  );
};

// Button Group Component
interface ButtonGroupProps {
  children: React.ReactNode;
  className?: string;
  attached?: boolean;
}

export const ButtonGroup: React.FC<ButtonGroupProps> = ({
  children,
  className,
  attached = false,
}) => {
  if (!attached) {
    return (
      <div className={clsx('flex items-center gap-2', className)}>
        {children}
      </div>
    );
  }

  return (
    <div className={clsx('inline-flex', className)}>
      {React.Children.map(children, (child, index) => {
        if (!React.isValidElement(child)) return child;

        const isFirst = index === 0;
        const isLast = index === React.Children.count(children) - 1;

        return React.cloneElement(child, {
          className: clsx(
            child.props.className,
            'rounded-none',
            isFirst && 'rounded-l-xl',
            isLast && 'rounded-r-xl',
            !isLast && 'border-r-0'
          ),
        } as React.HTMLAttributes<HTMLElement>);
      })}
    </div>
  );
};

export default Button;
