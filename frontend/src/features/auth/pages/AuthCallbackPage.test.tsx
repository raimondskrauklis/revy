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
        <Route path="/reviewer" element={<div>Reviewer</div>} />
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
      isUserLoading: false,
    } as unknown as ReturnType<typeof useAuth>);

    renderCallback();
    await waitFor(() => {
      expect(screen.getByText('Login')).toBeInTheDocument();
    });
  });

  it('waits for profile load before redirecting to reviewer', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      isUserLoading: true,
    } as unknown as ReturnType<typeof useAuth>);

    renderCallback();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(screen.queryByText('Reviewer')).not.toBeInTheDocument();
  });

  it('redirects to reviewer after profile load settles', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      isUserLoading: false,
    } as unknown as ReturnType<typeof useAuth>);

    renderCallback();
    await waitFor(() => {
      expect(screen.getByText('Reviewer')).toBeInTheDocument();
    });
  });
});
