// frontend/src/lib/router.tsx
import { RouterProvider, type RouterProviderProps } from 'react-router-dom';

export { ProtectedRoute } from '@/components/auth/ProtectedRoute';
export { RequirePermission } from '@/components/auth/RequirePermission';
export { AppShellLayout } from '@/components/layout/AppShellLayout';
export { NotFoundPage } from '@/components/errors/NotFoundPage';
export { LoginPage } from '@/features/auth/pages/LoginPage';
export { AuthCallbackPage } from '@/features/auth/pages/AuthCallbackPage';
export { UnauthorizedPage } from '@/features/auth/pages/UnauthorizedPage';
export { StatusGatePage } from '@/features/auth/pages/StatusGatePage';
export { DashboardPage } from '@/features/dashboard/pages/DashboardPage';

interface AppRouterProps {
  router: RouterProviderProps['router'];
}

export function AppRouter({ router }: AppRouterProps) {
  return <RouterProvider router={router} />;
}
