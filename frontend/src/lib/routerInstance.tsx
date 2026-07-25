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
import { RequirePermission } from '@/components/auth/RequirePermission';
import { SettingsLayout } from '@/features/settings/layout/SettingsLayout';
import { ProfileSettingsPage } from '@/features/settings/pages/ProfileSettingsPage';
import { SecuritySettingsPage } from '@/features/settings/pages/SecuritySettingsPage';
import { AppearanceSettingsPage } from '@/features/settings/pages/AppearanceSettingsPage';
import { WorkspaceSettingsPage } from '@/features/settings/pages/WorkspaceSettingsPage';
import { TeamSettingsPage } from '@/features/settings/pages/TeamSettingsPage';
import { IntegrationsSettingsPage } from '@/features/settings/pages/IntegrationsSettingsPage';
import { BillingSettingsPage } from '@/features/settings/pages/BillingSettingsPage';
import { DangerZonePage } from '@/features/settings/pages/DangerZonePage';
import { InstallationsPage } from '@/features/installations/pages/InstallationsPage';
import { adminRoutes } from '@/features/admin/routes';

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
    path: '/workspace-suspended',
    element: (
      <StatusGatePage
        titleKey="auth.status.workspaceSuspended.title"
        bodyKey="auth.status.workspaceSuspended.body"
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
            children: [
              { index: true, element: <Navigate to="/settings/profile" replace /> },
              { path: 'profile', element: <ProfileSettingsPage /> },
              { path: 'security', element: <SecuritySettingsPage /> },
              { path: 'appearance', element: <AppearanceSettingsPage /> },
              {
                element: <RequirePermission permission="admin:users" />,
                children: [{ path: 'workspace', element: <WorkspaceSettingsPage /> }],
              },
              { path: 'team', element: <TeamSettingsPage /> },
              { path: 'integrations', element: <IntegrationsSettingsPage /> },
              {
                element: <RequirePermission permission="admin:users" />,
                children: [{ path: 'billing', element: <BillingSettingsPage /> }],
              },
              { path: 'danger', element: <DangerZonePage /> },
            ],
          },
        ],
      },
      adminRoutes,
    ],
  },
  { path: '*', element: <NotFoundPage /> },
]);
