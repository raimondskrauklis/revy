// frontend/src/features/settings/pages/ProfileSettingsPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ProfileSettingsPage } from '@/features/settings/pages/ProfileSettingsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/lib/me', () => ({
  patchMe: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { patchMe } from '@/lib/me';

describe('ProfileSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders profile form and saves changes', async () => {
    const refetchUser = vi.fn().mockResolvedValue({
      id: '1',
      email: 'user@example.com',
      full_name: 'Ada',
      locale: 'lv',
      timezone: 'Europe/Riga',
      status: 'active',
      platform_role: null,
      workspace_id: 'ws-1',
      workspace_plan: null,
      role: AppRole.admin,
      memberships: [],
    });
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'Ada',
        locale: 'en',
        timezone: 'UTC',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: null,
        role: AppRole.admin,
        memberships: [],
      },
      refetchUser,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(patchMe).mockResolvedValue({
      id: '1',
      email: 'user@example.com',
      full_name: 'Ada',
      locale: 'lv',
      timezone: 'Europe/Riga',
      status: 'active',
      platform_role: null,
      workspace_id: 'ws-1',
      workspace_plan: null,
      role: AppRole.admin,
      memberships: [],
    });

    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    expect(screen.getByDisplayValue('user@example.com')).toBeDisabled();
    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
      expect(patchMe).toHaveBeenCalledWith({
        full_name: 'Ada',
        locale: 'en',
        timezone: 'UTC',
      });
    });
    expect(refetchUser).toHaveBeenCalled();
  });
});
