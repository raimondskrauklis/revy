// frontend/src/features/installations/pages/InstallationsPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { InstallationsPage } from '@/features/installations/pages/InstallationsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/installations/api', () => ({
  fetchInstallations: vi.fn(),
  registerInstallation: vi.fn(),
  connectInstallation: vi.fn(),
}));

vi.mock('@/shared/errors', () => ({
  mapApiError: vi.fn((error: unknown) => error),
}));

vi.mock('@/shared/errors/toasts', () => ({
  showDomainErrorToast: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import {
  connectInstallation,
  fetchInstallations,
  registerInstallation,
} from '@/features/installations/api';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

function adminUser(overrides: Record<string, unknown> = {}) {
  return {
    user: {
      id: '1',
      email: 'admin@example.com',
      full_name: 'Admin',
      status: 'active',
      platform_role: null,
      workspace_id: 'ws-1',
      role: AppRole.admin,
      memberships: [],
      ...overrides,
    },
  } as unknown as ReturnType<typeof useAuth>;
}

function renderPage(initialEntry = '/installations') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <InstallationsPage />
    </MemoryRouter>,
  );
}

describe('InstallationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchInstallations).mockResolvedValue([]);
  });

  it('shows empty state and Install Revy for an active admin', async () => {
    vi.mocked(useAuth).mockReturnValue(adminUser());

    renderPage();

    expect(await screen.findByText(/no github installations/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /install revy/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /register installation/i })).not.toBeInTheDocument();
  });

  it('hides connect CTA and fallback for viewers', async () => {
    vi.mocked(useAuth).mockReturnValue(
      adminUser({ id: '2', email: 'viewer@example.com', role: AppRole.viewer }),
    );

    renderPage();

    expect(await screen.findByText(/no github installations/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /install revy/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/register installation/i)).not.toBeInTheDocument();
  });

  it('starts connect without submitting a typed installation id', async () => {
    const user = userEvent.setup();
    const assign = vi.fn();
    vi.stubGlobal('location', { assign });
    vi.mocked(useAuth).mockReturnValue(adminUser());
    vi.mocked(connectInstallation).mockResolvedValue({
      install_url: 'https://github.com/apps/revy/installations/new?state=abc',
    });

    renderPage();
    await screen.findByRole('button', { name: /install revy/i });
    await user.click(screen.getByRole('button', { name: /install revy/i }));

    await waitFor(() => {
      expect(connectInstallation).toHaveBeenCalledWith('ws-1');
    });
    expect(assign).toHaveBeenCalledWith(
      'https://github.com/apps/revy/installations/new?state=abc',
    );
    expect(registerInstallation).not.toHaveBeenCalled();
  });

  it('surfaces setup_error from the hop return query', async () => {
    vi.mocked(useAuth).mockReturnValue(adminUser());

    renderPage('/installations?setup_error=invalid_state');

    expect(
      await screen.findByText(/github connect could not be completed/i),
    ).toBeInTheDocument();
  });

  it('toasts plan_upgrade_required from start-connect', async () => {
    const user = userEvent.setup();
    vi.mocked(useAuth).mockReturnValue(adminUser());
    const domainError = {
      code: 'plan_upgrade_required',
      message: 'Plan upgrade required',
      severity: 'info' as const,
      title: 'Request failed',
    };
    vi.mocked(connectInstallation).mockRejectedValue(domainError);
    vi.mocked(mapApiError).mockReturnValue(domainError);

    renderPage();
    await screen.findByRole('button', { name: /install revy/i });
    await user.click(screen.getByRole('button', { name: /install revy/i }));

    await waitFor(() => {
      expect(showDomainErrorToast).toHaveBeenCalledWith(domainError);
    });
    expect(registerInstallation).not.toHaveBeenCalled();
  });
});
