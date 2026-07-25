// frontend/src/features/settings/layout/SettingsSidebar.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SettingsSidebar } from '@/features/settings/layout/SettingsSidebar';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('SettingsSidebar', () => {
  it('hides admin-only workspace links for viewers', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'viewer@example.com',
        full_name: 'Viewer',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: 'free',
        role: AppRole.viewer,
        memberships: [],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <SettingsSidebar />
      </MemoryRouter>,
    );

    expect(screen.queryByRole('link', { name: /^workspace$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^billing$/i })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^team$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^danger zone$/i })).toBeInTheDocument();
  });

  it('shows admin workspace links for workspace admins', () => {
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
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <SettingsSidebar />
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: /^workspace$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^billing$/i })).toBeInTheDocument();
  });
});
