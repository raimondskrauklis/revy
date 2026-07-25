// frontend/src/features/settings/pages/SecuritySettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SecuritySettingsPage } from '@/features/settings/pages/SecuritySettingsPage';

vi.mock('@/lib/keycloak', () => ({
  getKeycloakAccountUrl: vi.fn(() => 'https://auth.example.com/realms/revy/account'),
}));

describe('SecuritySettingsPage', () => {
  it('links to Keycloak account console', () => {
    render(<SecuritySettingsPage />);

    const link = screen.getByRole('link', { name: /open account console/i });
    expect(link).toHaveAttribute('href', 'https://auth.example.com/realms/revy/account');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });
});
