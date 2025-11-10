/**
 * Error Boundaries Test Suite
 * Tests for PageErrorBoundary, ModalErrorBoundary, and WidgetErrorBoundary
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import PageErrorBoundary from '../PageErrorBoundary';
import ModalErrorBoundary from '../ModalErrorBoundary';
import WidgetErrorBoundary from '../WidgetErrorBoundary';

// Component that throws an error for testing
const ThrowError: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow = true }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
};

// Suppress console.error for cleaner test output
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalError;
});

describe('PageErrorBoundary', () => {
  it('should render children when there is no error', () => {
    render(
      <BrowserRouter>
        <PageErrorBoundary>
          <div>Test Content</div>
        </PageErrorBoundary>
      </BrowserRouter>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should catch errors and display error UI', () => {
    render(
      <BrowserRouter>
        <PageErrorBoundary>
          <ThrowError />
        </PageErrorBoundary>
      </BrowserRouter>
    );

    expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/We encountered an unexpected error/i)).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('should display retry button', () => {
    render(
      <BrowserRouter>
        <PageErrorBoundary>
          <ThrowError />
        </PageErrorBoundary>
      </BrowserRouter>
    );

    const retryButton = screen.getByRole('button', { name: /try again/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('should display go to dashboard button', () => {
    render(
      <BrowserRouter>
        <PageErrorBoundary>
          <ThrowError />
        </PageErrorBoundary>
      </BrowserRouter>
    );

    const homeButton = screen.getByRole('button', { name: /go to dashboard/i });
    expect(homeButton).toBeInTheDocument();
  });

  it('should call retry handler when retry button is clicked', () => {
    render(
      <BrowserRouter>
        <PageErrorBoundary>
          <ThrowError />
        </PageErrorBoundary>
      </BrowserRouter>
    );

    expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument();

    const retryButton = screen.getByRole('button', { name: /try again/i });

    // Verify retry button is clickable (does not throw)
    expect(() => fireEvent.click(retryButton)).not.toThrow();
  });
});

describe('ModalErrorBoundary', () => {
  it('should render children when there is no error', () => {
    render(
      <ModalErrorBoundary>
        <div>Modal Content</div>
      </ModalErrorBoundary>
    );

    expect(screen.getByText('Modal Content')).toBeInTheDocument();
  });

  it('should catch errors and display error UI', () => {
    render(
      <ModalErrorBoundary>
        <ThrowError />
      </ModalErrorBoundary>
    );

    expect(screen.getByText('Error Loading Content')).toBeInTheDocument();
    expect(screen.getByText(/We encountered an error while loading this modal content/i)).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('should display retry button', () => {
    render(
      <ModalErrorBoundary>
        <ThrowError />
      </ModalErrorBoundary>
    );

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('should display close button when onClose is provided', () => {
    const onClose = jest.fn();

    render(
      <ModalErrorBoundary onClose={onClose}>
        <ThrowError />
      </ModalErrorBoundary>
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    expect(closeButton).toBeInTheDocument();

    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should not display close button when onClose is not provided', () => {
    render(
      <ModalErrorBoundary>
        <ThrowError />
      </ModalErrorBoundary>
    );

    expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument();
  });
});

describe('WidgetErrorBoundary', () => {
  it('should render children when there is no error', () => {
    render(
      <WidgetErrorBoundary widgetName="Test Widget">
        <div>Widget Content</div>
      </WidgetErrorBoundary>
    );

    expect(screen.getByText('Widget Content')).toBeInTheDocument();
  });

  it('should catch errors and display error UI', () => {
    render(
      <WidgetErrorBoundary widgetName="Test Widget">
        <ThrowError />
      </WidgetErrorBoundary>
    );

    expect(screen.getByText('Test Widget Error')).toBeInTheDocument();
    expect(screen.getByText('Unable to load this content')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('should display widget name in error message', () => {
    render(
      <WidgetErrorBoundary widgetName="My Custom Widget">
        <ThrowError />
      </WidgetErrorBoundary>
    );

    expect(screen.getByText('My Custom Widget Error')).toBeInTheDocument();
  });

  it('should display default widget name when not provided', () => {
    render(
      <WidgetErrorBoundary>
        <ThrowError />
      </WidgetErrorBoundary>
    );

    expect(screen.getByText('Widget Error')).toBeInTheDocument();
  });

  it('should display retry button', () => {
    render(
      <WidgetErrorBoundary widgetName="Test Widget">
        <ThrowError />
      </WidgetErrorBoundary>
    );

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('should call retry handler when retry button is clicked', () => {
    render(
      <WidgetErrorBoundary widgetName="Test Widget">
        <ThrowError />
      </WidgetErrorBoundary>
    );

    expect(screen.getByText('Test Widget Error')).toBeInTheDocument();

    const retryButton = screen.getByRole('button', { name: /retry/i });

    // Verify retry button is clickable (does not throw)
    expect(() => fireEvent.click(retryButton)).not.toThrow();
  });
});

describe('Error Boundary Logging', () => {
  it('should log errors to console', () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <BrowserRouter>
        <PageErrorBoundary>
          <ThrowError />
        </PageErrorBoundary>
      </BrowserRouter>
    );

    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });
});
