import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import AppShell from './components/common/AppShell';
import { PageLoadingFallback } from './components/common/LoadingFallback';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// Lazy load all page components for route-based code splitting
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AgentStudio = lazy(() => import('./pages/AgentStudio'));
const ToolMarketplace = lazy(() => import('./pages/ToolMarketplace'));
const ExternalTools = lazy(() => import('./pages/ExternalTools'));
const ExecutionMonitor = lazy(() => import('./pages/ExecutionMonitor'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Templates = lazy(() => import('./pages/Templates'));
const NotFound = lazy(() => import('./pages/NotFound'));

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Suspense fallback={<PageLoadingFallback />}>
          <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell>
                <Dashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/agents"
          element={
            <ProtectedRoute>
              <AppShell>
                <AgentStudio />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/tools"
          element={
            <ProtectedRoute>
              <AppShell>
                <ToolMarketplace />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/external-tools"
          element={
            <ProtectedRoute>
              <AppShell>
                <ExternalTools />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/executions"
          element={
            <ProtectedRoute>
              <AppShell>
                <ExecutionMonitor />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <AppShell>
                <Analytics />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/templates"
          element={
            <ProtectedRoute>
              <AppShell>
                <Templates />
              </AppShell>
            </ProtectedRoute>
          }
        />

          {/* 404 route */}
          <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
