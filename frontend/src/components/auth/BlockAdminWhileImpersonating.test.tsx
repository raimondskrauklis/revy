// frontend/src/components/auth/BlockAdminWhileImpersonating.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { BlockAdminWhileImpersonating } from '@/components/auth/BlockAdminWhileImpersonating';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('BlockAdminWhileImpersonating', () => {
  it('redirects to dashboard when impersonating', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 'u1',
        email: 'target@example.com',
        impersonation: {
          active: true,
          actor_user_id: 'admin-1',
          target_user_id: 'u1',
          target_email: 'target@example.com',
          reason: 'Support investigation',
        },
      },
    } as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter initialEntries={['/admin/dashboard']}>
        <Routes>
          <Route element={<BlockAdminWhileImpersonating />}>
            <Route path="/admin/dashboard" element={<div>Admin page</div>} />
          </Route>
          <Route path="/dashboard" element={<div>Dashboard</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders child routes when not impersonating', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 'admin-1',
        email: 'admin@example.com',
        impersonation: null,
      },
    } as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter initialEntries={['/admin/dashboard']}>
        <Routes>
          <Route element={<BlockAdminWhileImpersonating />}>
            <Route path="/admin/dashboard" element={<div>Admin page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Admin page')).toBeInTheDocument();
  });
});
