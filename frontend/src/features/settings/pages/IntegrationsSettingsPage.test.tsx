// frontend/src/features/settings/pages/IntegrationsSettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { IntegrationsSettingsPage } from '@/features/settings/pages/IntegrationsSettingsPage';
import { AppRole } from '@/shared/types/enums';
import { clearExtensions, registerExtension } from '@/platform/extensions/registry';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/installations/RevyGitHubIntegrationCard', () => ({
  RevyGitHubIntegrationCard: () => <div>GitHub integration card</div>,
}));

import { useAuth } from '@/contexts/AuthContext';

describe('IntegrationsSettingsPage', () => {
  beforeEach(() => {
    clearExtensions();
    vi.clearAllMocks();
  });

  it('renders registered integration cards', () => {
    registerExtension({
      id: 'revy-github',
      slot: 'settings_integration',
      component: () => <div>GitHub integration card</div>,
      permission: 'items:view',
    });
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'viewer@example.com',
        full_name: null,
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.viewer,
        memberships: [],
      },
    } as unknown as ReturnType<typeof useAuth>);

    render(<IntegrationsSettingsPage />);

    expect(screen.getByText('GitHub integration card')).toBeInTheDocument();
  });

  it('shows empty state when no extensions are registered', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'viewer@example.com',
        full_name: null,
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.viewer,
        memberships: [],
      },
    } as unknown as ReturnType<typeof useAuth>);

    render(<IntegrationsSettingsPage />);

    expect(screen.getByText(/no integrations available/i)).toBeInTheDocument();
  });
});
