// frontend/src/App.tsx
import { ErrorBoundary } from '@/components/errors/ErrorBoundary';
import { AppRouter } from '@/lib/router';
import { appRouter } from '@/lib/routerInstance';

export default function App() {
  return (
    <ErrorBoundary>
      <AppRouter router={appRouter} />
    </ErrorBoundary>
  );
}
