// frontend/src/components/auth/RequirePlatformAdmin.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { RequirePlatformAdmin } from '@/components/auth/RequirePlatformAdmin';
import { AppRole, PlatformRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('RequirePlatformAdmin', () => {
  it('allows platform super_admin', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'sa@example.com',
        full_name: 'SA',
        status: 'active',
        platform_role: PlatformRole.super_admin,
        workspace_id: null,
        role: null,
        memberships: [],
      },
      isLoading: false,
      isUserLoading: false,
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<RequirePlatformAdmin />}>
            <Route path="/admin" element={<div>Admin area</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Admin area')).toBeInTheDocument();
  });

  it('shows loading while user profile is hydrating', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      isLoading: false,
      isUserLoading: true,
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<RequirePlatformAdmin />}>
            <Route path="/admin" element={<div>Admin area</div>} />
          </Route>
          <Route path="/unauthorized" element={<div>Denied</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.queryByText('Admin area')).not.toBeInTheDocument();
    expect(screen.queryByText('Denied')).not.toBeInTheDocument();
  });

  it('denies workspace admin without platform role', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '2',
        email: 'admin@example.com',
        full_name: 'Admin',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [],
      },
      isLoading: false,
      isUserLoading: false,
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<RequirePlatformAdmin />}>
            <Route path="/admin" element={<div>Admin area</div>} />
          </Route>
          <Route path="/unauthorized" element={<div>Denied</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Denied')).toBeInTheDocument();
  });
});
