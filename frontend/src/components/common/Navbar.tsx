import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHealthStatus } from '../../hooks/useMonitoring';
import { useAuth } from '../../hooks/useAuth';
import { ArrowRightOnRectangleIcon, Bars3Icon } from '@heroicons/react/24/outline';

interface NavbarProps {
  onMenuClick?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const { data: health } = useHealthStatus();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getUserInitials = () => {
    if (!user) return 'U';
    return user.username.substring(0, 2).toUpperCase();
  };

  return (
    <header className="bg-white border-b border-gray-200 px-4 sm:px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="lg:hidden -ml-2 p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Open sidebar"
        >
          <Bars3Icon className="h-6 w-6" />
        </button>

        <div className="flex-1 lg:flex-none">
          <h1 className="text-lg sm:text-2xl font-bold text-gray-900 truncate">
            DeepAgents Control Platform
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">
            Enterprise AI Agent Management
          </p>
        </div>

        <div className="flex items-center space-x-3 sm:space-x-4">
          {/* Health Status Indicator */}
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy'
                  ? 'bg-green-500'
                  : health?.status === 'degraded'
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-600">
              {health?.status || 'Unknown'}
            </span>
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="min-w-[44px] min-h-[44px] w-10 h-10 sm:w-10 sm:h-10 rounded-full bg-primary-600 flex items-center justify-center hover:bg-primary-700 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500"
              aria-label="User menu"
              aria-expanded={showUserMenu}
            >
              <span className="text-white text-sm font-medium">
                {getUserInitials()}
              </span>
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <>
                {/* Backdrop to close menu */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowUserMenu(false)}
                />

                <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
                  <div className="py-1">
                    {/* User Info */}
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="text-sm font-medium text-gray-900">
                        {user?.username}
                      </p>
                      <p className="text-sm text-gray-500 truncate">
                        {user?.email}
                      </p>
                    </div>

                    {/* Menu Items */}
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      <ArrowRightOnRectangleIcon className="h-5 w-5 mr-3 text-gray-400" />
                      Sign out
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
