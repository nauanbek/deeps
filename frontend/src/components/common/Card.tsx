import React from 'react';
import clsx from 'clsx';

export type CardVariant = 'default' | 'interactive' | 'gradient' | 'glass' | 'outlined';
export type CardPadding = 'none' | 'sm' | 'md' | 'lg';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: CardVariant;
  padding?: CardPadding;
  onClick?: () => void;
  hover?: boolean;
}

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-white rounded-2xl border border-surface-200/60 shadow-card',
  interactive: clsx(
    'bg-white rounded-2xl border border-surface-200/60 shadow-card cursor-pointer',
    'hover:shadow-card-hover hover:border-surface-300 hover:-translate-y-0.5',
    'active:translate-y-0 active:shadow-card'
  ),
  gradient: 'bg-gradient-to-br from-white to-surface-50 rounded-2xl border border-surface-200/60 shadow-card',
  glass: 'backdrop-blur-xl rounded-2xl border border-white/20 bg-white/80',
  outlined: 'bg-transparent rounded-2xl border-2 border-surface-200 border-dashed',
};

const paddingStyles: Record<CardPadding, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  padding = 'md',
  onClick,
  hover = false,
}) => {
  const Component = onClick ? 'button' : 'div';
  const isInteractive = onClick || variant === 'interactive';

  return (
    <Component
      className={clsx(
        'transition-all duration-300',
        variantStyles[variant],
        paddingStyles[padding],
        hover && !isInteractive && 'hover:shadow-soft-lg hover:-translate-y-0.5',
        onClick && 'text-left w-full',
        className
      )}
      onClick={onClick}
      type={onClick ? 'button' : undefined}
    >
      {children}
    </Component>
  );
};

// Card Header Component
interface CardHeaderProps {
  title: string;
  subtitle?: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  description,
  action,
  icon,
  badge,
  className,
}) => {
  return (
    <div className={clsx('flex items-start justify-between gap-4 mb-4', className)}>
      <div className="flex items-start gap-3 min-w-0">
        {icon && (
          <div className="flex-shrink-0 p-2 rounded-xl bg-primary-100 text-primary-600">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-surface-900 truncate">
              {title}
            </h3>
            {badge}
          </div>
          {subtitle && (
            <p className="text-sm text-surface-500 mt-0.5">{subtitle}</p>
          )}
          {description && (
            <p className="text-sm text-surface-600 mt-1 line-clamp-2">{description}</p>
          )}
        </div>
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
};

// Card Footer Component
interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
  bordered?: boolean;
}

export const CardFooter: React.FC<CardFooterProps> = ({
  children,
  className,
  bordered = true,
}) => {
  return (
    <div
      className={clsx(
        'flex items-center justify-end gap-3 mt-4 pt-4',
        bordered && 'border-t border-surface-100',
        className
      )}
    >
      {children}
    </div>
  );
};

// Card Content Component
interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className,
}) => {
  return <div className={clsx('', className)}>{children}</div>;
};

// Stat Card Component
interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
}

const statVariantStyles = {
  default: 'bg-surface-100 text-surface-600',
  primary: 'bg-primary-100 text-primary-600',
  success: 'bg-success-100 text-success-600',
  warning: 'bg-warning-100 text-warning-600',
  error: 'bg-error-100 text-error-600',
};

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  change,
  changeLabel,
  icon,
  trend,
  variant = 'default',
}) => {
  const trendColor =
    trend === 'up'
      ? 'text-success-600'
      : trend === 'down'
      ? 'text-error-600'
      : 'text-surface-500';

  return (
    <Card className="relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 w-24 h-24 bg-gradient-to-br from-primary-500/5 to-transparent rounded-full" />

      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-surface-500">{label}</span>
          {icon && (
            <span className={clsx('p-2 rounded-xl', statVariantStyles[variant])}>
              {icon}
            </span>
          )}
        </div>
        <div className="flex items-end justify-between">
          <span className="text-3xl font-bold text-surface-900 tracking-tight">
            {value}
          </span>
          {change !== undefined && (
            <div className={clsx('flex items-center gap-1 text-sm font-medium', trendColor)}>
              {trend && trend !== 'neutral' && (
                <svg
                  className={clsx('w-4 h-4', trend === 'down' && 'rotate-180')}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              <span>{Math.abs(change)}%</span>
              {changeLabel && (
                <span className="text-surface-400 font-normal">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

// Feature Card Component
interface FeatureCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  action?: React.ReactNode;
  variant?: 'default' | 'primary' | 'accent';
}

const featureIconStyles = {
  default: 'bg-surface-100 text-surface-600',
  primary: 'bg-primary-100 text-primary-600',
  accent: 'bg-accent-100 text-accent-600',
};

export const FeatureCard: React.FC<FeatureCardProps> = ({
  title,
  description,
  icon,
  action,
  variant = 'primary',
}) => {
  return (
    <Card variant="interactive" className="group">
      <div className={clsx(
        'inline-flex p-3 rounded-xl mb-4 transition-transform group-hover:scale-110',
        featureIconStyles[variant]
      )}>
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-surface-900 mb-2">{title}</h3>
      <p className="text-surface-500 text-sm mb-4 line-clamp-2">{description}</p>
      {action}
    </Card>
  );
};

export default Card;
