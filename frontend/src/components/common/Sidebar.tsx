import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  CpuChipIcon,
  PlayCircleIcon,
  ChartBarIcon,
  WrenchIcon,
  DocumentDuplicateIcon,
  ServerStackIcon,
} from '@heroicons/react/24/outline';

interface NavItemProps {
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon: Icon, label }) => {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
          isActive
            ? 'bg-primary-600 text-white'
            : 'text-gray-700 hover:bg-gray-100'
        }`
      }
    >
      <Icon className="w-5 h-5" />
      <span className="font-medium">{label}</span>
    </NavLink>
  );
};

export const Sidebar: React.FC = () => {
  return (
    <aside className="hidden lg:flex w-64 bg-white border-r border-gray-200 flex-col">
      <div className="p-6">
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <CpuChipIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">DeepAgents</h2>
            <p className="text-xs text-gray-500">Control Platform</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-2">
        <NavItem to="/" icon={HomeIcon} label="Dashboard" />
        <NavItem to="/agents" icon={CpuChipIcon} label="Agents" />
        <NavItem to="/templates" icon={DocumentDuplicateIcon} label="Templates" />
        <NavItem to="/tools" icon={WrenchIcon} label="Custom Tools" />
        <NavItem to="/external-tools" icon={ServerStackIcon} label="External Tools" />
        <NavItem to="/executions" icon={PlayCircleIcon} label="Executions" />
        <NavItem to="/analytics" icon={ChartBarIcon} label="Analytics" />
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <div>Version 0.1.0</div>
          <div className="mt-1">deepagents v0.2.5+</div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
