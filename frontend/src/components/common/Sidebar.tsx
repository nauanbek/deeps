import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import {
  HomeIcon,
  CpuChipIcon,
  PlayCircleIcon,
  ChartBarIcon,
  WrenchIcon,
  DocumentDuplicateIcon,
  ServerStackIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface NavItem {
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  badge?: number | string;
}

const navItems: NavItem[] = [
  { to: '/', icon: HomeIcon, label: 'Dashboard' },
  { to: '/agents', icon: CpuChipIcon, label: 'Agents' },
  { to: '/templates', icon: DocumentDuplicateIcon, label: 'Templates' },
  { to: '/tools', icon: WrenchIcon, label: 'Custom Tools' },
  { to: '/external-tools', icon: ServerStackIcon, label: 'External Tools' },
  { to: '/executions', icon: PlayCircleIcon, label: 'Executions' },
  { to: '/analytics', icon: ChartBarIcon, label: 'Analytics' },
];

interface NavItemComponentProps {
  item: NavItem;
}

const NavItemComponent: React.FC<NavItemComponentProps> = ({ item }) => {
  const { to, icon: Icon, label, badge } = item;

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          'group flex items-center gap-3 px-4 py-3 rounded-xl font-medium',
          'transition-all duration-200',
          isActive
            ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg shadow-primary-500/25'
            : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
        )
      }
      aria-current={({ isActive }) => (isActive ? 'page' : undefined)}
    >
      <Icon
        className={clsx(
          'w-5 h-5 flex-shrink-0 transition-transform',
          'group-hover:scale-110'
        )}
      />
      <span className="flex-1 truncate">{label}</span>
      {badge !== undefined && (
        <span
          className={clsx(
            'flex-shrink-0 min-w-[20px] h-5 px-1.5 text-xs font-bold rounded-full',
            'flex items-center justify-center'
          )}
        >
          {badge}
        </span>
      )}
    </NavLink>
  );
};

export const Sidebar: React.FC = () => {
  return (
    <aside className="hidden lg:flex w-72 bg-white border-r border-surface-200 flex-col">
      {/* Logo */}
      <div className="px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-11 h-11 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-success-500 rounded-full border-2 border-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-surface-900 tracking-tight">
              DeepAgents
            </h1>
            <p className="text-xs text-surface-500">Control Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto scrollbar-thin">
        {navItems.map((item) => (
          <NavItemComponent key={item.to} item={item} />
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-surface-100">
        <div className="px-4 py-3 rounded-xl bg-gradient-to-r from-surface-50 to-surface-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-surface-200 flex items-center justify-center">
              <CpuChipIcon className="w-4 h-4 text-surface-500" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-surface-700 truncate">
                deepagents
              </p>
              <p className="text-xs text-surface-500">v0.2.5</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
