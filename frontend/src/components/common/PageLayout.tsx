import React from 'react';
import clsx from 'clsx';

interface PageLayoutProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '7xl' | 'full';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const maxWidthStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '7xl': 'max-w-7xl',
  full: 'max-w-full',
};

const paddingStyles = {
  none: 'px-0 py-0',
  sm: 'px-4 py-4',
  md: 'px-4 sm:px-6 lg:px-8 py-6',
  lg: 'px-4 sm:px-6 lg:px-8 py-8',
};

export const PageLayout: React.FC<PageLayoutProps> = ({
  children,
  className,
  maxWidth = '7xl',
  padding = 'lg',
}) => {
  return (
    <div
      className={clsx(
        'mx-auto w-full animate-fade-in',
        maxWidthStyles[maxWidth],
        paddingStyles[padding],
        className
      )}
    >
      {children}
    </div>
  );
};

// Page Header Component
interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  action,
  breadcrumbs,
  className,
}) => {
  return (
    <div className={clsx('mb-8', className)}>
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="mb-4" aria-label="Breadcrumb">
          <ol className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <li key={crumb.label} className="flex items-center gap-2">
                {index > 0 && (
                  <svg
                    className="w-4 h-4 text-surface-300"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
                {crumb.href ? (
                  <a
                    href={crumb.href}
                    className="text-surface-500 hover:text-surface-700 transition-colors"
                  >
                    {crumb.label}
                  </a>
                ) : (
                  <span className="text-surface-900 font-medium">{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1 text-surface-500">{subtitle}</p>
          )}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
    </div>
  );
};

// Page Section Component
interface PageSectionProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const PageSection: React.FC<PageSectionProps> = ({
  children,
  title,
  subtitle,
  action,
  className,
  noPadding = false,
}) => {
  return (
    <section className={clsx('mb-8', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-surface-900">{title}</h2>
            )}
            {subtitle && (
              <p className="mt-0.5 text-sm text-surface-500">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={clsx(!noPadding && 'card p-6')}>{children}</div>
    </section>
  );
};

// Stats Grid Component
interface StatItem {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
}

interface StatsGridProps {
  stats: StatItem[];
  columns?: 2 | 3 | 4;
}

export const StatsGrid: React.FC<StatsGridProps> = ({ stats, columns = 4 }) => {
  const columnStyles = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={clsx('grid gap-4 mb-8', columnStyles[columns])}>
      {stats.map((stat) => (
        <div key={stat.label} className="card p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-surface-500">{stat.label}</span>
            {stat.icon && (
              <span className="p-2 rounded-lg bg-primary-100 text-primary-600">
                {stat.icon}
              </span>
            )}
          </div>
          <div className="flex items-end justify-between">
            <span className="text-2xl font-bold text-surface-900">{stat.value}</span>
            {stat.change !== undefined && (
              <span
                className={clsx(
                  'text-sm font-medium flex items-center gap-1',
                  stat.change >= 0 ? 'text-success-600' : 'text-error-600'
                )}
              >
                <svg
                  className={clsx('w-4 h-4', stat.change < 0 && 'rotate-180')}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                {Math.abs(stat.change)}%
                {stat.changeLabel && (
                  <span className="text-surface-400 ml-1">{stat.changeLabel}</span>
                )}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default PageLayout;
