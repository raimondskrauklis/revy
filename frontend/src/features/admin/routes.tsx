// frontend/src/features/admin/routes.tsx
import { Navigate } from 'react-router-dom';
import { RequirePlatformAdmin } from '@/components/auth/RequirePlatformAdmin';
import { BlockAdminWhileImpersonating } from '@/components/auth/BlockAdminWhileImpersonating';
import { AdminLayout } from '@/features/admin/layout/AdminLayout';
import { AdminDashboardPage } from '@/features/admin/pages/AdminDashboardPage';
import { AdminSettingsPage } from '@/features/admin/pages/AdminSettingsPage';
import { AdminUsersPage } from '@/features/admin/pages/AdminUsersPage';
import { AuditSearchPage } from '@/features/admin/pages/AuditSearchPage';
import { WorkspaceDetailPage } from '@/features/admin/pages/WorkspaceDetailPage';
import { WorkspacesPage } from '@/features/admin/pages/WorkspacesPage';

export const adminRoutes = {
  element: <RequirePlatformAdmin />,
  children: [
    {
      element: <BlockAdminWhileImpersonating />,
      children: [
        {
          path: '/admin',
          element: <AdminLayout />,
          children: [
            { index: true, element: <Navigate to="/admin/dashboard" replace /> },
            { path: 'dashboard', element: <AdminDashboardPage /> },
            { path: 'workspaces', element: <WorkspacesPage /> },
            { path: 'workspaces/:workspaceId', element: <WorkspaceDetailPage /> },
            { path: 'users', element: <AdminUsersPage /> },
            { path: 'audit', element: <AuditSearchPage /> },
            { path: 'settings', element: <AdminSettingsPage /> },
          ],
        },
      ],
    },
  ],
};
