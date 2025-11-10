import React from 'react';

// Export a mockable navigate function
export const mockNavigate = jest.fn();

export const useNavigate = () => mockNavigate;
export const useParams = () => ({});
export const useLocation = () => ({ pathname: '/' });
export const Link = ({ children, to }: any) => React.createElement('a', { href: to }, children);
export const Navigate = ({ to }: any) => React.createElement('div', {}, `Redirected to ${to}`);
export const BrowserRouter = ({ children }: any) => React.createElement('div', {}, children);
export const Routes = ({ children }: any) => React.createElement('div', {}, children);
export const Route = ({ element }: any) => React.createElement('div', {}, element);
