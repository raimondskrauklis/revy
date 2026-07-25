// frontend/src/features/admin/pages/AdminSettingsPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { AdminSettingsPage } from '@/features/admin/pages/AdminSettingsPage';

vi.mock('@/features/admin/api', () => ({
  fetchAdminSettings: vi.fn(),
}));

vi.mock('@/lib/keycloak', () => ({
  getKeycloakAdminConsoleUrl: vi.fn(() => 'https://auth.example.com/admin/revy/console/'),
}));

import { fetchAdminSettings } from '@/features/admin/api';

describe('AdminSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders registration flags', async () => {
    vi.mocked(fetchAdminSettings).mockResolvedValue({
      registration_require_admin_approval: true,
      registration_require_profile_form: false,
    });

    render(<AdminSettingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/require admin approval/i)).toBeInTheDocument();
      expect(screen.getByText(/^yes$/i)).toBeInTheDocument();
      expect(screen.getByText(/^no$/i)).toBeInTheDocument();
    });
  });

  it('renders keycloak admin link', async () => {
    vi.mocked(fetchAdminSettings).mockResolvedValue({
      registration_require_admin_approval: false,
      registration_require_profile_form: false,
    });

    render(<AdminSettingsPage />);

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /keycloak admin console/i });
      expect(link).toHaveAttribute('href', 'https://auth.example.com/admin/revy/console/');
    });
  });
});
