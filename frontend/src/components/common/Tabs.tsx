import React from 'react';
import clsx from 'clsx';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: number | string;
  disabled?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'pills' | 'underline' | 'boxed';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  className?: string;
}

const variantStyles = {
  pills: {
    container: 'flex gap-1 p-1 bg-surface-100 rounded-xl',
    tab: 'rounded-lg',
    active: 'bg-white text-surface-900 shadow-sm',
    inactive: 'text-surface-600 hover:text-surface-900 hover:bg-surface-200/50',
  },
  underline: {
    container: 'flex gap-0 border-b border-surface-200',
    tab: 'border-b-2 -mb-px',
    active: 'border-primary-600 text-primary-600',
    inactive: 'border-transparent text-surface-500 hover:text-surface-700 hover:border-surface-300',
  },
  boxed: {
    container: 'flex gap-0 border border-surface-200 rounded-xl overflow-hidden',
    tab: 'border-r border-surface-200 last:border-r-0',
    active: 'bg-primary-600 text-white',
    inactive: 'bg-white text-surface-600 hover:bg-surface-50',
  },
};

const sizeStyles = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  variant = 'pills',
  size = 'md',
  fullWidth = false,
  className,
}) => {
  const styles = variantStyles[variant];

  return (
    <div
      className={clsx(styles.container, fullWidth && 'w-full', className)}
      role="tablist"
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-controls={`tabpanel-${tab.id}`}
          onClick={() => !tab.disabled && onChange(tab.id)}
          disabled={tab.disabled}
          className={clsx(
            'flex items-center justify-center gap-2 font-medium transition-all duration-200',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            styles.tab,
            sizeStyles[size],
            fullWidth && 'flex-1',
            activeTab === tab.id ? styles.active : styles.inactive
          )}
        >
          {tab.icon && <span className="flex-shrink-0">{tab.icon}</span>}
          <span>{tab.label}</span>
          {tab.badge !== undefined && (
            <span
              className={clsx(
                'min-w-[20px] h-5 px-1.5 text-xs font-bold rounded-full flex items-center justify-center',
                activeTab === tab.id
                  ? variant === 'pills'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-white/20 text-current'
                  : 'bg-surface-200 text-surface-600'
              )}
            >
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

// Tab Panel Component
interface TabPanelProps {
  id: string;
  activeTab: string;
  children: React.ReactNode;
  className?: string;
}

export const TabPanel: React.FC<TabPanelProps> = ({
  id,
  activeTab,
  children,
  className,
}) => {
  if (activeTab !== id) return null;

  return (
    <div
      id={`tabpanel-${id}`}
      role="tabpanel"
      aria-labelledby={id}
      tabIndex={0}
      className={clsx('animate-fade-in', className)}
    >
      {children}
    </div>
  );
};

// Vertical Tabs
interface VerticalTabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export const VerticalTabs: React.FC<VerticalTabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className,
}) => {
  return (
    <div className={clsx('flex flex-col gap-1', className)} role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          onClick={() => !tab.disabled && onChange(tab.id)}
          disabled={tab.disabled}
          className={clsx(
            'flex items-center gap-3 px-4 py-3 rounded-xl text-left font-medium',
            'transition-all duration-200',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            activeTab === tab.id
              ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/25'
              : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900'
          )}
        >
          {tab.icon && <span className="flex-shrink-0 w-5 h-5">{tab.icon}</span>}
          <span className="flex-1">{tab.label}</span>
          {tab.badge !== undefined && (
            <span
              className={clsx(
                'min-w-[20px] h-5 px-1.5 text-xs font-bold rounded-full flex items-center justify-center',
                activeTab === tab.id
                  ? 'bg-white/20 text-current'
                  : 'bg-surface-200 text-surface-600'
              )}
            >
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
