import React from 'react';

// Export a mockable navigate function
export const mockNavigate = jest.fn();

export const useNavigate = () => mockNavigate;
export const useParams = () => ({});
export const useLocation = () => ({ pathname: '/' });
export const Link = ({ children, to }: { children: React.ReactNode; to: string }) => React.createElement('a', { href: to }, children);
export const Navigate = ({ to }: { to: string }) => React.createElement('div', {}, `Redirected to ${to}`);
export const BrowserRouter = ({ children }: { children: React.ReactNode }) => React.createElement('div', {}, children);
export const Routes = ({ children }: { children: React.ReactNode }) => React.createElement('div', {}, children);
export const Route = ({ element }: { element: React.ReactNode }) => React.createElement('div', {}, element);
