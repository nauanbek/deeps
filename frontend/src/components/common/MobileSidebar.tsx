import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import {
  HomeIcon,
  CpuChipIcon,
  PlayCircleIcon,
  ChartBarIcon,
  WrenchIcon,
  DocumentDuplicateIcon,
  ServerStackIcon,
  XMarkIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
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
  onClick: () => void;
}

const NavItemComponent: React.FC<NavItemComponentProps> = ({ item, onClick }) => {
  const { to, icon: Icon, label } = item;

  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        clsx(
          'group flex items-center gap-3 px-4 py-3 rounded-xl font-medium',
          'transition-all duration-200',
          isActive
            ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg shadow-primary-500/25'
            : 'text-surface-600 hover:text-surface-900 hover:bg-surface-100'
        )
      }
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <span>{label}</span>
    </NavLink>
  );
};

export const MobileSidebar: React.FC<MobileSidebarProps> = ({ isOpen, onClose }) => {
  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50 lg:hidden" onClose={onClose}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="transition-opacity ease-linear duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="transition-opacity ease-linear duration-300"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-surface-900/60 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 flex">
          {/* Sliding panel */}
          <Transition.Child
            as={Fragment}
            enter="transition ease-in-out duration-300 transform"
            enterFrom="-translate-x-full"
            enterTo="translate-x-0"
            leave="transition ease-in-out duration-300 transform"
            leaveFrom="translate-x-0"
            leaveTo="-translate-x-full"
          >
            <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
              {/* Close button */}
              <Transition.Child
                as={Fragment}
                enter="ease-in-out duration-300"
                enterFrom="opacity-0"
                enterTo="opacity-100"
                leave="ease-in-out duration-300"
                leaveFrom="opacity-100"
                leaveTo="opacity-0"
              >
                <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                  <button
                    type="button"
                    className="p-2.5 rounded-xl bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-colors"
                    onClick={onClose}
                    aria-label="Close sidebar"
                  >
                    <span className="sr-only">Close sidebar</span>
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </div>
              </Transition.Child>

              {/* Sidebar content */}
              <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4 shadow-2xl">
                {/* Logo */}
                <div className="flex h-20 shrink-0 items-center pt-6">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="w-11 h-11 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25">
                        <SparklesIcon className="w-6 h-6 text-white" />
                      </div>
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-success-500 rounded-full border-2 border-white" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-surface-900 tracking-tight">
                        DeepAgents
                      </h2>
                      <p className="text-xs text-surface-500">Control Platform</p>
                    </div>
                  </div>
                </div>

                {/* Navigation */}
                <nav className="flex flex-1 flex-col">
                  <ul role="list" className="flex flex-1 flex-col gap-y-7">
                    <li>
                      <ul role="list" className="space-y-1">
                        {navItems.map((item) => (
                          <li key={item.to}>
                            <NavItemComponent item={item} onClick={onClose} />
                          </li>
                        ))}
                      </ul>
                    </li>

                    {/* Version info */}
                    <li className="mt-auto">
                      <div className="px-4 py-3 rounded-xl bg-gradient-to-r from-surface-50 to-surface-100">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-surface-200 flex items-center justify-center">
                            <CpuChipIcon className="w-4 h-4 text-surface-500" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-surface-700">
                              deepagents
                            </p>
                            <p className="text-xs text-surface-500">v0.2.5</p>
                          </div>
                        </div>
                      </div>
                    </li>
                  </ul>
                </nav>
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

export default MobileSidebar;
