// frontend/src/platform/extensions/WidgetErrorBoundary.tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

function WidgetErrorFallback() {
  const { t } = useTranslation();
  return (
    <div
      className="rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]"
      role="alert"
    >
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('dashboard.widgetError')}</p>
    </div>
  );
}

export class WidgetErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('WidgetErrorBoundary', error, info.componentStack);
    }
  }

  render() {
    if (this.state.hasError) {
      return <WidgetErrorFallback />;
    }
    return this.props.children;
  }
}
