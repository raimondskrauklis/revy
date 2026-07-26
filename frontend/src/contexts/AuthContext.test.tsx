// frontend/src/contexts/AuthContext.test.tsx
import { render, waitFor } from '@testing-library/react';
import { AxiosError } from 'axios';
import { useEffect } from 'react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';

vi.mock('@/lib/keycloak', () => ({
  initKeycloak: vi.fn(() => ({
    init: vi.fn().mockResolvedValue(true),
    login: vi.fn(),
    logout: vi.fn(),
  })),
  resetKeycloak: vi.fn(),
  setKeycloakInitialized: vi.fn(),
}));

vi.mock('@/lib/me', () => ({
  fetchMe: vi.fn(),
  syncStoredWorkspace: vi.fn((user: unknown) => user),
}));

vi.mock('@/shared/errors/toasts', () => ({
  notify: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  showDomainErrorToast: vi.fn(),
}));

import { fetchMe } from '@/lib/me';
import { showDomainErrorToast } from '@/shared/errors/toasts';

function RefetchOnAuth() {
  const { refetchUser, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      void refetchUser();
    }
  }, [isAuthenticated, refetchUser]);

  return null;
}

function axiosError(status: number, body: Record<string, unknown>) {
  return new AxiosError('request failed', undefined, undefined, undefined, {
    status,
    data: body,
    headers: {},
    config: {} as never,
    statusText: 'Error',
  });
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows toast when /me fails with provision_email_required', async () => {
    vi.mocked(fetchMe).mockRejectedValue(
      axiosError(401, {
        error: 'provision_email_required',
        message: 'Email is required to provision your account',
      }),
    );

    render(
      <AuthProvider>
        <RefetchOnAuth />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(showDomainErrorToast).toHaveBeenCalledWith(
        expect.objectContaining({ code: 'provision_email_required' }),
      );
    });
  });

  it('shows toast when /me fails with identity_email_conflict', async () => {
    vi.mocked(fetchMe).mockRejectedValue(
      axiosError(409, {
        error: 'identity_email_conflict',
        message: 'Email is already associated with another account',
      }),
    );

    render(
      <AuthProvider>
        <RefetchOnAuth />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(showDomainErrorToast).toHaveBeenCalledWith(
        expect.objectContaining({ code: 'identity_email_conflict' }),
      );
    });
  });
});
