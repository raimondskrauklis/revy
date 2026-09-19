// frontend/src/features/auth/pages/UnauthorizedPage.test.tsx
import { render, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { UnauthorizedPage } from '@/features/auth/pages/UnauthorizedPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

function renderUnauthorized(state?: { reason?: string }) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/unauthorized', state }]}>
      <Routes>
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route path="/reviewer" element={<div>Reviewer</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('UnauthorizedPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading while profile is still fetching', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      logout: vi.fn(),
      isUserLoading: true,
    } as unknown as ReturnType<typeof useAuth>);

    renderUnauthorized();
    expect(document.body.textContent).toContain('Loading');
    expect(document.body.textContent).not.toContain("Couldn't load your account");
  });

  it('redirects active users to reviewer when not permission denied', async () => {
    vi.mocked(useAuth).mockReturnValue({
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
      logout: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    renderUnauthorized();
    await waitFor(() => {
      expect(document.body.textContent).toContain('Reviewer');
    });
  });

  it('stays on page for permission denied even when user exists', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'Test User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.viewer,
        memberships: [],
      },
      logout: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    renderUnauthorized({ reason: 'permission' });
    await waitFor(() => {
      expect(document.body.textContent).toContain('Access denied');
    });
    expect(document.body.textContent).not.toContain('Reviewer');
  });
});
