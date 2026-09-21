// frontend/src/features/settings/pages/BillingSettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { BillingSettingsPage } from '@/features/settings/pages/BillingSettingsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/settings/hooks', () => ({
  useBillingStatus: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { useBillingStatus } from '@/features/settings/hooks';

function renderPage(initialEntry = '/settings/billing') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <BillingSettingsPage />
    </MemoryRouter>,
  );
}

function mockUser() {
  vi.mocked(useAuth).mockReturnValue({
    user: {
      id: '1',
      email: 'admin@example.com',
      full_name: 'Admin',
      status: 'active',
      platform_role: null,
      workspace_id: 'ws-1',
      role: AppRole.admin,
      memberships: [],
      locale: 'en',
      timezone: 'UTC',
    },
  } as unknown as ReturnType<typeof useAuth>);
}

describe('BillingSettingsPage', () => {
  it('shows current plan badge', () => {
    mockUser();
    vi.mocked(useBillingStatus).mockReturnValue({
      data: { plan: 'free', stripe_enabled: false },
      isLoading: false,
    } as unknown as ReturnType<typeof useBillingStatus>);

    renderPage();

    expect(screen.getByText(/Free/i)).toBeInTheDocument();
  });

  it('shows not-configured message when stripe is disabled', () => {
    mockUser();
    vi.mocked(useBillingStatus).mockReturnValue({
      data: { plan: 'free', stripe_enabled: false },
      isLoading: false,
    } as unknown as ReturnType<typeof useBillingStatus>);

    renderPage();

    expect(screen.getByText(/not available/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /upgrade/i })).not.toBeInTheDocument();
  });
});