import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { UserPlusIcon, UserIcon, EnvelopeIcon, LockClosedIcon } from '@heroicons/react/24/outline';
import { Input } from '../components/common/Input';
import { PasswordStrengthMeter } from '../components/common/PasswordStrengthMeter';

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
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-100 px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-primary-600 rounded-xl flex items-center justify-center">
              <UserPlusIcon className="h-10 w-10 text-white" aria-hidden="true" />
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Join DeepAgents Control Platform
          </p>
        </div>

        <div className="bg-white py-8 px-6 shadow-lg rounded-xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {apiError && (
              <div className="rounded-md bg-red-50 p-4" role="alert">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-red-800">{apiError}</p>
                  </div>
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
              icon={<UserIcon className="h-5 w-5" />}
              iconPosition="left"
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
              icon={<EnvelopeIcon className="h-5 w-5" />}
              iconPosition="left"
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
                icon={<LockClosedIcon className="h-5 w-5" />}
                iconPosition="left"
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
              icon={<LockClosedIcon className="h-5 w-5" />}
              iconPosition="left"
            />

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center min-h-[48px] py-2.5 px-4 border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" aria-hidden="true"></div>
                    Creating account...
                  </div>
                ) : (
                  'Create account'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Already have an account?</span>
              </div>
            </div>

            <div className="mt-6">
              <Link
                to="/login"
                className="w-full inline-flex justify-center min-h-[48px] items-center py-2.5 px-4 border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500 transition-colors"
              >
                Sign in instead
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default Register;
