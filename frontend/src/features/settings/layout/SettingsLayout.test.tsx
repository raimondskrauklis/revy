// frontend/src/features/settings/layout/SettingsLayout.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SettingsLayout } from '@/features/settings/layout/SettingsLayout';
import { ProfileSettingsPage } from '@/features/settings/pages/ProfileSettingsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('SettingsLayout', () => {
  it('renders personal and workspace nav links for workspace admins', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: 'pro',
        role: AppRole.admin,
        memberships: [],
        locale: 'en',
        timezone: 'UTC',
      },
      refetchUser: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter initialEntries={['/settings/profile']}>
        <Routes>
          <Route path="/settings" element={<SettingsLayout />}>
            <Route path="profile" element={<ProfileSettingsPage />} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('navigation', { name: /settings sections/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^profile$/i })).toHaveAttribute(
      'href',
      '/settings/profile',
    );
    expect(screen.getByRole('link', { name: /^security$/i })).toHaveAttribute(
      'href',
      '/settings/security',
    );
    expect(screen.getByRole('link', { name: /^appearance$/i })).toHaveAttribute(
      'href',
      '/settings/appearance',
    );
    expect(screen.getByRole('link', { name: /^workspace$/i })).toHaveAttribute(
      'href',
      '/settings/workspace',
    );
    expect(screen.getByRole('link', { name: /^team$/i })).toHaveAttribute('href', '/settings/team');
    expect(screen.getByRole('link', { name: /^integrations$/i })).toHaveAttribute(
      'href',
      '/settings/integrations',
    );
  });
});
