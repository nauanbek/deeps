import React, { useState, useId } from 'react';
import clsx from 'clsx';
import { EyeIcon, EyeSlashIcon, ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

export type InputSize = 'sm' | 'md' | 'lg';
export type InputVariant = 'default' | 'filled' | 'outlined';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  helperText?: string;
  success?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  inputSize?: InputSize;
  variant?: InputVariant;
  showPasswordToggle?: boolean;
  clearable?: boolean;
  onClear?: () => void;
  containerClassName?: string;
}

const sizeStyles: Record<InputSize, { input: string; icon: string; label: string }> = {
  sm: {
    input: 'px-3 py-2 text-sm rounded-lg',
    icon: 'w-4 h-4',
    label: 'text-xs',
  },
  md: {
    input: 'px-4 py-2.5 text-sm rounded-xl',
    icon: 'w-5 h-5',
    label: 'text-sm',
  },
  lg: {
    input: 'px-4 py-3 text-base rounded-xl',
    icon: 'w-5 h-5',
    label: 'text-sm',
  },
};

const variantStyles: Record<InputVariant, { default: string; error: string; success: string }> = {
  default: {
    default: clsx(
      'bg-white border border-surface-200',
      'focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500'
    ),
    error: clsx(
      'bg-white border border-error-300',
      'focus:ring-2 focus:ring-error-500/20 focus:border-error-500'
    ),
    success: clsx(
      'bg-white border border-success-300',
      'focus:ring-2 focus:ring-success-500/20 focus:border-success-500'
    ),
  },
  filled: {
    default: clsx(
      'bg-surface-100 border border-transparent',
      'focus:bg-white focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500'
    ),
    error: clsx(
      'bg-error-50 border border-transparent',
      'focus:bg-white focus:ring-2 focus:ring-error-500/20 focus:border-error-500'
    ),
    success: clsx(
      'bg-success-50 border border-transparent',
      'focus:bg-white focus:ring-2 focus:ring-success-500/20 focus:border-success-500'
    ),
  },
  outlined: {
    default: clsx(
      'bg-transparent border-2 border-surface-200',
      'focus:ring-0 focus:border-primary-500'
    ),
    error: clsx(
      'bg-transparent border-2 border-error-300',
      'focus:ring-0 focus:border-error-500'
    ),
    success: clsx(
      'bg-transparent border-2 border-success-300',
      'focus:ring-0 focus:border-success-500'
    ),
  },
};

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      success = false,
      icon,
      iconPosition = 'left',
      inputSize = 'md',
      variant = 'default',
      showPasswordToggle = false,
      clearable = false,
      onClear,
      className,
      containerClassName,
      type = 'text',
      disabled,
      required,
      id,
      ...props
    },
    ref
  ) => {
    const autoId = useId();
    const inputId = id || autoId;
    const [showPassword, setShowPassword] = useState(false);

    const hasError = Boolean(error);
    const hasSuccess = success && !hasError;
    const isPassword = type === 'password';
    const actualType = isPassword && showPassword ? 'text' : type;

    const sizes = sizeStyles[inputSize];
    const variants = variantStyles[variant];
    const stateStyle = hasError ? variants.error : hasSuccess ? variants.success : variants.default;

    const hasLeftIcon = icon && iconPosition === 'left';
    const hasRightContent =
      (icon && iconPosition === 'right') ||
      (isPassword && showPasswordToggle) ||
      clearable ||
      hasError ||
      hasSuccess;

    return (
      <div className={clsx('w-full', containerClassName)}>
        {/* Label */}
        {label && (
          <label
            htmlFor={inputId}
            className={clsx(
              'block font-medium text-surface-700 mb-1.5',
              sizes.label,
              disabled && 'opacity-50'
            )}
          >
            {label}
            {required && <span className="text-error-500 ml-0.5">*</span>}
          </label>
        )}

        {/* Input wrapper */}
        <div className="relative">
          {/* Left icon */}
          {hasLeftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className={clsx('text-surface-400', sizes.icon)} aria-hidden="true">
                {icon}
              </span>
            </div>
          )}

          {/* Input */}
          <input
            ref={ref}
            id={inputId}
            type={actualType}
            disabled={disabled}
            required={required}
            className={clsx(
              'w-full',
              'text-surface-900 placeholder:text-surface-400',
              'focus:outline-none',
              'disabled:bg-surface-50 disabled:text-surface-500 disabled:cursor-not-allowed',
              'transition-all duration-200',
              sizes.input,
              stateStyle,
              hasLeftIcon && 'pl-10',
              hasRightContent && 'pr-10',
              className
            )}
            aria-invalid={hasError}
            aria-describedby={
              error
                ? `${inputId}-error`
                : helperText
                ? `${inputId}-helper`
                : undefined
            }
            {...props}
          />

          {/* Right content */}
          {hasRightContent && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center gap-1">
              {/* Status icons */}
              {hasError && !isPassword && (
                <ExclamationCircleIcon className={clsx('text-error-500', sizes.icon)} />
              )}
              {hasSuccess && !isPassword && (
                <CheckCircleIcon className={clsx('text-success-500', sizes.icon)} />
              )}

              {/* Password toggle */}
              {isPassword && showPasswordToggle && (
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={clsx(
                    'p-1 rounded-lg text-surface-400 hover:text-surface-600',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                    'transition-colors'
                  )}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeSlashIcon className={sizes.icon} />
                  ) : (
                    <EyeIcon className={sizes.icon} />
                  )}
                </button>
              )}

              {/* Clear button */}
              {clearable && props.value && (
                <button
                  type="button"
                  onClick={onClear}
                  className={clsx(
                    'p-1 rounded-lg text-surface-400 hover:text-surface-600',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                    'transition-colors'
                  )}
                  aria-label="Clear input"
                >
                  <svg className={sizes.icon} viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              )}

              {/* Right icon */}
              {icon && iconPosition === 'right' && !hasError && !hasSuccess && (
                <span className={clsx('text-surface-400', sizes.icon)} aria-hidden="true">
                  {icon}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Error message */}
        {error && (
          <p
            id={`${inputId}-error`}
            className="mt-1.5 text-sm text-error-600 flex items-center gap-1"
            role="alert"
          >
            <ExclamationCircleIcon className="w-4 h-4 flex-shrink-0" />
            {error}
          </p>
        )}

        {/* Helper text */}
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="mt-1.5 text-sm text-surface-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// Form Group Component
interface FormGroupProps {
  children: React.ReactNode;
  className?: string;
  horizontal?: boolean;
}

export const FormGroup: React.FC<FormGroupProps> = ({
  children,
  className,
  horizontal = false,
}) => {
  return (
    <div
      className={clsx(
        horizontal ? 'flex items-start gap-4' : 'space-y-4',
        className
      )}
    >
      {children}
    </div>
  );
};

// Input with Addon
interface InputAddonProps extends InputProps {
  addonBefore?: React.ReactNode;
  addonAfter?: React.ReactNode;
}

export const InputAddon = React.forwardRef<HTMLInputElement, InputAddonProps>(
  ({ addonBefore, addonAfter, className, inputSize = 'md', ...props }, ref) => {
    const sizes = sizeStyles[inputSize];

    return (
      <div className="flex">
        {addonBefore && (
          <div
            className={clsx(
              'inline-flex items-center px-3 border border-r-0 border-surface-200',
              'bg-surface-50 text-surface-500 text-sm',
              'rounded-l-xl'
            )}
          >
            {addonBefore}
          </div>
        )}
        <Input
          ref={ref}
          inputSize={inputSize}
          className={clsx(
            addonBefore && 'rounded-l-none',
            addonAfter && 'rounded-r-none',
            className
          )}
          {...props}
        />
        {addonAfter && (
          <div
            className={clsx(
              'inline-flex items-center px-3 border border-l-0 border-surface-200',
              'bg-surface-50 text-surface-500 text-sm',
              'rounded-r-xl'
            )}
          >
            {addonAfter}
          </div>
        )}
      </div>
    );
  }
);

InputAddon.displayName = 'InputAddon';

export default Input;
