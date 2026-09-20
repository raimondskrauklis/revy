// frontend/src/lib/router.tsx
import { RouterProvider, type RouterProviderProps } from 'react-router-dom';

export { ProtectedRoute } from '@/components/auth/ProtectedRoute';
export { UnauthorizedPage } from '@/features/auth/pages/UnauthorizedPage';
export { StatusGatePage } from '@/features/auth/pages/StatusGatePage';
export { DashboardPage } from '@/features/dashboard/pages/DashboardPage';

interface AppRouterProps {
  router: RouterProviderProps['router'];
}

export function AppRouter({ router }: AppRouterProps) {
  return <RouterProvider router={router} />;
}
