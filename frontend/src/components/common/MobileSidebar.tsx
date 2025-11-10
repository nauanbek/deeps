import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  CpuChipIcon,
  PlayCircleIcon,
  ChartBarIcon,
  WrenchIcon,
  DocumentDuplicateIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItemProps {
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon: Icon, label, onClick }) => {
  return (
    <NavLink
      to={to}
      onClick={onClick}
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
          <div className="fixed inset-0 bg-gray-900/80" />
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
                    className="-m-2.5 p-2.5"
                    onClick={onClose}
                    aria-label="Close sidebar"
                  >
                    <span className="sr-only">Close sidebar</span>
                    <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                  </button>
                </div>
              </Transition.Child>

              {/* Sidebar content */}
              <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4">
                {/* Logo */}
                <div className="flex h-16 shrink-0 items-center pt-6">
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

                {/* Navigation */}
                <nav className="flex flex-1 flex-col">
                  <ul role="list" className="flex flex-1 flex-col gap-y-7">
                    <li>
                      <ul role="list" className="space-y-2">
                        <li>
                          <NavItem to="/" icon={HomeIcon} label="Dashboard" onClick={onClose} />
                        </li>
                        <li>
                          <NavItem to="/agents" icon={CpuChipIcon} label="Agents" onClick={onClose} />
                        </li>
                        <li>
                          <NavItem to="/templates" icon={DocumentDuplicateIcon} label="Templates" onClick={onClose} />
                        </li>
                        <li>
                          <NavItem to="/tools" icon={WrenchIcon} label="Tools" onClick={onClose} />
                        </li>
                        <li>
                          <NavItem to="/executions" icon={PlayCircleIcon} label="Executions" onClick={onClose} />
                        </li>
                        <li>
                          <NavItem to="/analytics" icon={ChartBarIcon} label="Analytics" onClick={onClose} />
                        </li>
                      </ul>
                    </li>

                    {/* Version info */}
                    <li className="mt-auto border-t border-gray-200 pt-4">
                      <div className="text-xs text-gray-500">
                        <div>Version 0.1.0</div>
                        <div className="mt-1">deepagents v0.2.5+</div>
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
