// frontend/src/features/settings/pages/BillingSettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { BillingSettingsPage } from '@/features/settings/pages/BillingSettingsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/settings/hooks', () => ({
  useBillingStatus: vi.fn(),
  useCreateCheckoutSession: vi.fn(),
  useCreatePortalSession: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import {
  useBillingStatus,
  useCreateCheckoutSession,
  useCreatePortalSession,
} from '@/features/settings/hooks';

function renderPage(initialEntry = '/settings/billing') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <BillingSettingsPage />
    </MemoryRouter>,
  );
}

describe('BillingSettingsPage', () => {
  it('shows not-configured copy when stripe is disabled', () => {
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
    vi.mocked(useBillingStatus).mockReturnValue({
      data: { plan: 'free', stripe_enabled: false },
      isLoading: false,
    } as unknown as ReturnType<typeof useBillingStatus>);
    vi.mocked(useCreateCheckoutSession).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCheckoutSession>);
    vi.mocked(useCreatePortalSession).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreatePortalSession>);

    renderPage();

    expect(screen.getByText(/billing is not configured/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /upgrade/i })).not.toBeInTheDocument();
  });

  it('shows upgrade button when stripe is enabled on free plan', () => {
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
    vi.mocked(useBillingStatus).mockReturnValue({
      data: { plan: 'free', stripe_enabled: true },
      isLoading: false,
    } as unknown as ReturnType<typeof useBillingStatus>);
    vi.mocked(useCreateCheckoutSession).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCheckoutSession>);
    vi.mocked(useCreatePortalSession).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreatePortalSession>);

    renderPage();

    expect(screen.getByRole('button', { name: /upgrade/i })).toBeInTheDocument();
  });

  it('redirects to checkout url on upgrade', async () => {
    const user = userEvent.setup();
    const assignMock = vi.fn();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { assign: assignMock },
    });

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
    vi.mocked(useBillingStatus).mockReturnValue({
      data: { plan: 'free', stripe_enabled: true },
      isLoading: false,
    } as unknown as ReturnType<typeof useBillingStatus>);
    vi.mocked(useCreateCheckoutSession).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({ url: 'https://checkout.stripe.test' }),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCheckoutSession>);
    vi.mocked(useCreatePortalSession).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreatePortalSession>);

    renderPage();

    await user.click(screen.getByRole('button', { name: /upgrade/i }));

    expect(assignMock).toHaveBeenCalledWith('https://checkout.stripe.test');
  });
});
