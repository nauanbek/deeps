import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  widgetName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class WidgetErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(
      `Widget Error Boundary caught an error in ${this.props.widgetName || 'widget'}:`,
      error,
      errorInfo
    );

    // Optional: Send to error tracking service
    // Sentry.captureException(error, {
    //   contexts: { react: errorInfo },
    //   tags: { widget: this.props.widgetName || 'unknown' }
    // });
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="bg-white rounded-lg shadow p-6 border-2 border-red-200">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg
                className="w-5 h-5 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-gray-900">
                {this.props.widgetName || 'Widget'} Error
              </h3>
              <p className="mt-1 text-xs text-gray-600">
                Unable to load this content
              </p>
              {this.state.error && (
                <p className="mt-2 text-xs text-red-600 font-mono truncate">
                  {this.state.error.message}
                </p>
              )}
              <button
                onClick={this.handleRetry}
                className="mt-3 inline-flex items-center px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 rounded hover:bg-primary-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              >
                <svg
                  className="w-3 h-3 mr-1.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Retry
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default WidgetErrorBoundary;
