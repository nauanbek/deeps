import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { useAuth } from '../hooks/useAuth';
import {
  LockClosedIcon,
  UserIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [apiError, setApiError] = useState<string>('');

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');

    if (!validateForm()) {
      return;
    }

    try {
      await login(formData.username, formData.password);
      navigate('/');
    } catch (error: unknown) {
      console.error('Login error:', error);
      let message = 'Invalid username or password';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        message = axiosError.response?.data?.detail || message;
      }
      setApiError(message);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (apiError) {
      setApiError('');
    }
  };

  return (
    <main className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900">
        {/* Background patterns */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full blur-3xl transform -translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent-400 rounded-full blur-3xl transform translate-x-1/2 translate-y-1/2" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-14 h-14 bg-white/10 backdrop-blur-sm rounded-2xl flex items-center justify-center">
              <SparklesIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">DeepAgents</h1>
              <p className="text-white/60 text-sm">Control Platform</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold mb-4 leading-tight">
            Enterprise AI Agent
            <br />
            Management Platform
          </h2>
          <p className="text-white/70 text-lg max-w-md">
            Create, configure, and manage AI agents with a visual development environment.
            Powered by deepagents framework.
          </p>

          {/* Features */}
          <div className="mt-12 space-y-4">
            {[
              'Visual agent configuration',
              'Real-time execution monitoring',
              'External tools integration',
              'Advanced analytics & insights',
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-success-500/20 flex items-center justify-center">
                  <svg className="w-3 h-3 text-success-400" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <span className="text-white/80">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 bg-surface-50">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex justify-center mb-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25">
                <SparklesIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-surface-900">DeepAgents</h1>
                <p className="text-xs text-surface-500">Control Platform</p>
              </div>
            </div>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
              Welcome back
            </h2>
            <p className="mt-2 text-surface-500">
              Sign in to your account to continue
            </p>
          </div>

          {/* Form card */}
          <div className="card p-8">
            <form className="space-y-6" onSubmit={handleSubmit}>
              {/* API Error */}
              {apiError && (
                <div
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-xl',
                    'bg-error-50 border border-error-200 text-error-700'
                  )}
                  role="alert"
                >
                  <ExclamationTriangleIcon className="w-5 h-5 flex-shrink-0" />
                  <p className="text-sm font-medium">{apiError}</p>
                </div>
              )}

              {/* Form fields */}
              <div className="space-y-5">
                <Input
                  id="username"
                  name="username"
                  type="text"
                  label="Username"
                  autoComplete="username"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  error={errors.username}
                  icon={<UserIcon className="h-5 w-5" />}
                  iconPosition="left"
                  placeholder="Enter your username"
                  inputSize="lg"
                />

                <Input
                  id="password"
                  name="password"
                  type="password"
                  label="Password"
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  error={errors.password}
                  icon={<LockClosedIcon className="h-5 w-5" />}
                  iconPosition="left"
                  placeholder="Enter your password"
                  showPasswordToggle
                  inputSize="lg"
                />
              </div>

              {/* Submit button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isLoading}
              >
                Sign in
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-surface-200" />
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 bg-white text-sm text-surface-500">
                  New to DeepAgents?
                </span>
              </div>
            </div>

            {/* Register link */}
            <Link to="/register">
              <Button variant="secondary" size="lg" fullWidth>
                Create an account
              </Button>
            </Link>
          </div>

          {/* Footer */}
          <p className="mt-8 text-center text-sm text-surface-500">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </main>
  );
};

export default Login;
