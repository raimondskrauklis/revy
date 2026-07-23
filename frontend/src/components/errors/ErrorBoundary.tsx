// frontend/src/components/errors/ErrorBoundary.tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Sentry } from '@/lib/sentry';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

function ErrorFallback() {
  const { t } = useTranslation();
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[color:var(--app-canvas)] p-6 text-center"
      role="alert"
    >
      <p className="text-[color:var(--app-text-strong)] text-lg font-semibold">
        {t('errors.unknown_error')}
      </p>
      <button
        type="button"
        className="h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        onClick={() => window.location.reload()}
      >
        {t('common.retry')}
      </button>
    </div>
  );
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary', error, info.componentStack);
    }

    Sentry.captureException(error, {
      extra: {
        componentStack: info.componentStack,
      },
    });
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
