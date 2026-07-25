// frontend/src/lib/routerInstance.tsx
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShellLayout } from '@/components/layout/AppShellLayout';
import { NotFoundPage } from '@/components/errors/NotFoundPage';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { AuthCallbackPage } from '@/features/auth/pages/AuthCallbackPage';
import { UnauthorizedPage } from '@/features/auth/pages/UnauthorizedPage';
import { CompleteProfilePage } from '@/features/auth/pages/CompleteProfilePage';
import { StatusGatePage } from '@/features/auth/pages/StatusGatePage';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { AdminUsersPage } from '@/features/admin/pages/AdminUsersPage';
import { RequirePlatformAdmin } from '@/components/auth/RequirePlatformAdmin';
import { SettingsLayout } from '@/features/settings/layout/SettingsLayout';
import { SettingsShellPage } from '@/features/settings/pages/SettingsShellPage';
import { InstallationsPage } from '@/features/installations/pages/InstallationsPage';

export const appRouter = createBrowserRouter([
  { path: '/', element: <Navigate to="/dashboard" replace /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/auth/callback', element: <AuthCallbackPage /> },
  {
    path: '/auth/verify-email',
    element: (
      <StatusGatePage
        titleKey="auth.status.verifyEmail.title"
        bodyKey="auth.status.verifyEmail.body"
      />
    ),
  },
  {
    path: '/complete-profile',
    element: <CompleteProfilePage />,
  },
  {
    path: '/pending-approval',
    element: (
      <StatusGatePage
        titleKey="auth.status.pendingApproval.title"
        bodyKey="auth.status.pendingApproval.body"
      />
    ),
  },
  {
    path: '/account-rejected',
    element: (
      <StatusGatePage
        titleKey="auth.status.rejected.title"
        bodyKey="auth.status.rejected.body"
      />
    ),
  },
  {
    path: '/account-suspended',
    element: (
      <StatusGatePage
        titleKey="auth.status.suspended.title"
        bodyKey="auth.status.suspended.body"
      />
    ),
  },
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: '/dashboard',
        element: <AppShellLayout />,
        children: [{ index: true, element: <DashboardPage /> }],
      },
      {
        path: '/installations',
        element: <AppShellLayout />,
        children: [{ index: true, element: <InstallationsPage /> }],
      },
      {
        path: '/settings',
        element: <AppShellLayout />,
        children: [
          {
            element: <SettingsLayout />,
            children: [{ index: true, element: <SettingsShellPage /> }],
          },
        ],
      },
      {
        element: <RequirePlatformAdmin />,
        children: [
          {
            path: '/admin/users',
            element: <AppShellLayout />,
            children: [{ index: true, element: <AdminUsersPage /> }],
          },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
]);
