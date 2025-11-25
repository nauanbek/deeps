import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import clsx from 'clsx';
import { useHealthStatus } from '../../hooks/useMonitoring';
import { useAuth } from '../../hooks/useAuth';
import {
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  BellIcon,
  Cog6ToothIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';

interface NavbarProps {
  onMenuClick?: () => void;
}

const statusConfig = {
  healthy: {
    color: 'bg-success-500',
    ring: 'ring-success-500/20',
    label: 'All systems operational',
  },
  degraded: {
    color: 'bg-warning-500',
    ring: 'ring-warning-500/20',
    label: 'Degraded performance',
  },
  unhealthy: {
    color: 'bg-error-500',
    ring: 'ring-error-500/20',
    label: 'System issues detected',
  },
};

export const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const { data: health } = useHealthStatus();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getUserInitials = () => {
    if (!user) return 'U';
    return user.username.substring(0, 2).toUpperCase();
  };

  const status = health?.status || 'unhealthy';
  const statusInfo = statusConfig[status as keyof typeof statusConfig] || statusConfig.unhealthy;

  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-lg border-b border-surface-200/60">
      <div className="px-4 sm:px-6 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Left section */}
          <div className="flex items-center gap-3">
            {/* Mobile menu button */}
            <button
              onClick={onMenuClick}
              className={clsx(
                'lg:hidden p-2.5 rounded-xl',
                'text-surface-600 hover:text-surface-900 hover:bg-surface-100',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                'transition-colors'
              )}
              aria-label="Open sidebar"
            >
              <Bars3Icon className="h-5 w-5" />
            </button>

            {/* Page title - hidden on desktop (shown in sidebar) */}
            <div className="lg:hidden">
              <h1 className="text-lg font-bold text-surface-900">
                DeepAgents
              </h1>
            </div>
          </div>

          {/* Right section */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Health Status */}
            <div
              className={clsx(
                'hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full',
                'bg-surface-50 border border-surface-200'
              )}
              title={statusInfo.label}
            >
              <span className="relative flex h-2 w-2">
                <span
                  className={clsx(
                    'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                    statusInfo.color
                  )}
                />
                <span
                  className={clsx(
                    'relative inline-flex rounded-full h-2 w-2',
                    statusInfo.color
                  )}
                />
              </span>
              <span className="text-xs font-medium text-surface-600 capitalize">
                {status}
              </span>
            </div>

            {/* Mobile health indicator */}
            <div
              className={clsx(
                'sm:hidden relative flex h-2.5 w-2.5 rounded-full',
                statusInfo.color
              )}
              title={statusInfo.label}
            />

            {/* Notifications */}
            <button
              className={clsx(
                'relative p-2.5 rounded-xl',
                'text-surface-500 hover:text-surface-700 hover:bg-surface-100',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                'transition-colors'
              )}
              aria-label="View notifications"
            >
              <BellIcon className="h-5 w-5" />
              {/* Notification badge */}
              <span className="absolute top-2 right-2 w-2 h-2 bg-error-500 rounded-full" />
            </button>

            {/* User Menu */}
            <Menu as="div" className="relative">
              <Menu.Button
                className={clsx(
                  'flex items-center gap-2 p-1.5 pr-3 rounded-xl',
                  'bg-surface-50 hover:bg-surface-100 border border-surface-200',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                  'transition-colors'
                )}
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-sm">
                  <span className="text-white text-xs font-semibold">
                    {getUserInitials()}
                  </span>
                </div>
                <span className="hidden sm:block text-sm font-medium text-surface-700 max-w-[120px] truncate">
                  {user?.username}
                </span>
                <svg
                  className="hidden sm:block w-4 h-4 text-surface-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </Menu.Button>

              <Transition
                as={Fragment}
                enter="transition ease-out duration-200"
                enterFrom="opacity-0 scale-95 translate-y-1"
                enterTo="opacity-100 scale-100 translate-y-0"
                leave="transition ease-in duration-150"
                leaveFrom="opacity-100 scale-100 translate-y-0"
                leaveTo="opacity-0 scale-95 translate-y-1"
              >
                <Menu.Items className="absolute right-0 mt-2 w-64 rounded-xl shadow-dropdown bg-white border border-surface-200 focus:outline-none overflow-hidden">
                  {/* User Info */}
                  <div className="px-4 py-4 bg-gradient-to-r from-surface-50 to-surface-100">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20">
                        <span className="text-white text-base font-semibold">
                          {getUserInitials()}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-surface-900 truncate">
                          {user?.username}
                        </p>
                        <p className="text-xs text-surface-500 truncate">
                          {user?.email}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Menu Items */}
                  <div className="py-1">
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          className={clsx(
                            'w-full flex items-center gap-3 px-4 py-2.5 text-sm',
                            active ? 'bg-surface-50 text-surface-900' : 'text-surface-700'
                          )}
                        >
                          <UserCircleIcon className="h-5 w-5 text-surface-400" />
                          Profile
                        </button>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          className={clsx(
                            'w-full flex items-center gap-3 px-4 py-2.5 text-sm',
                            active ? 'bg-surface-50 text-surface-900' : 'text-surface-700'
                          )}
                        >
                          <Cog6ToothIcon className="h-5 w-5 text-surface-400" />
                          Settings
                        </button>
                      )}
                    </Menu.Item>
                  </div>

                  <div className="border-t border-surface-100">
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={handleLogout}
                          className={clsx(
                            'w-full flex items-center gap-3 px-4 py-2.5 text-sm',
                            active ? 'bg-error-50 text-error-700' : 'text-surface-700'
                          )}
                        >
                          <ArrowRightOnRectangleIcon className="h-5 w-5 text-surface-400" />
                          Sign out
                        </button>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
