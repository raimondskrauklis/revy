// frontend/src/features/auth/pages/AuthCallbackPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { AuthCallbackPage } from '@/features/auth/pages/AuthCallbackPage';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

function renderCallback() {
  return render(
    <MemoryRouter initialEntries={['/auth/callback']}>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/login" element={<div>Login</div>} />
        <Route path="/dashboard" element={<div>Dashboard</div>} />
        <Route path="/unauthorized" element={<div>Unauthorized</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('AuthCallbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects to login when not authenticated', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      refetchUser: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    renderCallback();
    await waitFor(() => {
      expect(screen.getByText('Login')).toBeInTheDocument();
    });
  });

  it('redirects to dashboard when profile loads', async () => {
    const refetchUser = vi.fn().mockResolvedValue({ id: '1' });
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      refetchUser,
    } as unknown as ReturnType<typeof useAuth>);

    renderCallback();
    await waitFor(() => {
      expect(refetchUser).toHaveBeenCalled();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });

  it('redirects to unauthorized when profile fails to load', async () => {
    const refetchUser = vi.fn().mockResolvedValue(null);
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      refetchUser,
    } as unknown as ReturnType<typeof useAuth>);

    renderCallback();
    await waitFor(() => {
      expect(refetchUser).toHaveBeenCalled();
      expect(screen.getByText('Unauthorized')).toBeInTheDocument();
    });
  });
});
