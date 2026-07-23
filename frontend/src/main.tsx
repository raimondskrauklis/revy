// frontend/src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/contexts/AuthContext';
import { queryClient } from '@/lib/queryClient';
import { initSentry } from '@/lib/sentry';
import { configureErrorHandling } from '@/shared/errors/handlers';
import App from './App';
import './index.css';
import './i18n/config';

initSentry();

configureErrorHandling({
  login: () => {
    window.location.href = '/login';
  },
  unauthorizedPath: '/unauthorized',
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <App />
        <Toaster
          position="bottom-center"
          richColors
          closeButton
          toastOptions={{ style: { zIndex: 'var(--z-toast)' } }}
        />
      </QueryClientProvider>
    </AuthProvider>
  </StrictMode>,
);
