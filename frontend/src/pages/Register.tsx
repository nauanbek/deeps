import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { useAuth } from '../hooks/useAuth';
import {
  UserPlusIcon,
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
  CheckIcon,
  SparklesIcon,
  CpuChipIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { PasswordStrengthMeter } from '../components/common/PasswordStrengthMeter';

const features = [
  { icon: CpuChipIcon, text: 'Create and manage AI agents' },
  { icon: ChartBarIcon, text: 'Real-time execution monitoring' },
  { icon: ShieldCheckIcon, text: 'Enterprise-grade security' },
];

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [apiError, setApiError] = useState<string>('');

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    } else if (formData.username.length > 50) {
      newErrors.username = 'Username must be less than 50 characters';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, hyphens, and underscores';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-zA-Z])(?=.*[0-9])/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one letter and one number';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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
      await register(formData.username, formData.email, formData.password);
      navigate('/');
    } catch (error: unknown) {
      console.error('Registration error:', error);

      // Handle validation errors (422)
      let message = 'Registration failed. Please try again.';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: unknown } } };
        const detail = axiosError.response?.data?.detail;

        // If detail is an array of validation errors
        if (Array.isArray(detail)) {
          message = detail
            .map((err: { msg?: string } | unknown) =>
              typeof err === 'object' && err !== null && 'msg' in err
                ? err.msg
                : JSON.stringify(err)
            )
            .join(', ');
        }
        // If detail is a string
        else if (typeof detail === 'string') {
          message = detail;
        }
        // If detail is an object
        else if (typeof detail === 'object' && detail !== null) {
          const detailObj = detail as { msg?: string };
          message = detailObj.msg || JSON.stringify(detail);
        }
      }

      setApiError(message);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    // Clear API error on input change
    if (apiError) {
      setApiError('');
    }
  };

  return (
    <main className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-700 to-accent-600 p-12 flex-col justify-between relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full -translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 right-0 w-80 h-80 bg-white rounded-full translate-x-1/3 translate-y-1/3" />
          <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-white rounded-full -translate-x-1/2 -translate-y-1/2" />
        </div>

        {/* Content */}
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <SparklesIcon className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">DeepAgents</span>
          </div>
          <p className="text-primary-100 text-lg">Control Platform</p>
        </div>

        <div className="relative z-10 space-y-8">
          <div>
            <h2 className="text-4xl font-bold text-white mb-4">
              Join the future of AI automation
            </h2>
            <p className="text-primary-100 text-lg leading-relaxed">
              Create an account to start building and managing your AI agents with enterprise-grade tools.
            </p>
          </div>

          <div className="space-y-4">
            {features.map((feature, index) => (
              <div key={index} className="flex items-center gap-4 text-white">
                <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <feature.icon className="w-5 h-5" />
                </div>
                <span className="text-lg">{feature.text}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-primary-200 text-sm">
            Trusted by leading organizations worldwide
          </p>
        </div>
      </div>

      {/* Right Panel - Registration Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 bg-surface-50">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25">
              <SparklesIcon className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-surface-900">DeepAgents</span>
          </div>

          {/* Form Card */}
          <div className="bg-white rounded-2xl shadow-card p-8 border border-surface-100">
            <div className="text-center mb-8">
              <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/25">
                <UserPlusIcon className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-surface-900">Create your account</h1>
              <p className="text-surface-500 mt-2">Join DeepAgents Control Platform</p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              {/* API Error Alert */}
              {apiError && (
                <div className="rounded-xl bg-error-50 border border-error-200 p-4" role="alert">
                  <div className="flex items-start gap-3">
                    <ExclamationCircleIcon className="w-5 h-5 text-error-500 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-error-700">{apiError}</p>
                  </div>
                </div>
              )}

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
                placeholder="Choose a username"
                icon={<UserIcon className="w-5 h-5" />}
                iconPosition="left"
                inputSize="lg"
              />

              <Input
                id="email"
                name="email"
                type="email"
                label="Email address"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                error={errors.email}
                placeholder="you@example.com"
                icon={<EnvelopeIcon className="w-5 h-5" />}
                iconPosition="left"
                inputSize="lg"
              />

              <div>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  label="Password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  error={errors.password}
                  placeholder="Create a strong password"
                  icon={<LockClosedIcon className="w-5 h-5" />}
                  iconPosition="left"
                  inputSize="lg"
                  showPasswordToggle
                />
                <div className="mt-2">
                  <PasswordStrengthMeter password={formData.password} />
                </div>
              </div>

              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                label="Confirm password"
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                error={errors.confirmPassword}
                placeholder="Re-enter your password"
                icon={<LockClosedIcon className="w-5 h-5" />}
                iconPosition="left"
                inputSize="lg"
                showPasswordToggle
                success={formData.confirmPassword.length > 0 && formData.password === formData.confirmPassword}
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isLoading}
              >
                Create account
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-surface-200" />
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 bg-white text-sm text-surface-500">
                  Already have an account?
                </span>
              </div>
            </div>

            {/* Sign In Link */}
            <Link to="/login">
              <Button variant="secondary" size="lg" fullWidth>
                Sign in instead
              </Button>
            </Link>
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-surface-500 mt-6">
            By creating an account, you agree to our{' '}
            <a href="#" className="text-primary-600 hover:text-primary-700 font-medium">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="#" className="text-primary-600 hover:text-primary-700 font-medium">
              Privacy Policy
            </a>
          </p>
        </div>
      </div>
    </main>
  );
};

export default Register;
