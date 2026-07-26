// frontend/src/components/auth/ProtectedRoute.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route path="/login" element={<div>Login</div>} />
        <Route path="/unauthorized" element={<div>Unauthorized</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<div>Dashboard</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects to login when not authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      isUserLoading: false,
      user: null,
    } as unknown as ReturnType<typeof useAuth>);

    renderProtectedRoute();
    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('redirects to unauthorized when authenticated but profile missing', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      isUserLoading: false,
      user: null,
    } as unknown as ReturnType<typeof useAuth>);

    renderProtectedRoute();
    expect(screen.getByText('Unauthorized')).toBeInTheDocument();
  });

  it('renders child route when authenticated with active user', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      isUserLoading: false,
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'Test User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [],
      },
    } as unknown as ReturnType<typeof useAuth>);

    renderProtectedRoute();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });
});
