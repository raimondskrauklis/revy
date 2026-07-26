// frontend/src/features/settings/pages/SecuritySettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { SecuritySettingsPage } from '@/features/settings/pages/SecuritySettingsPage';

const openKeycloakAccountConsole = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    keycloak: {
      createAccountUrl: vi.fn(() => 'https://auth.example.com/realms/revy/account?client=revy-web'),
    },
  })),
}));

vi.mock('@/lib/keycloak', () => ({
  openKeycloakAccountConsole: (...args: unknown[]) => openKeycloakAccountConsole(...args),
}));

describe('SecuritySettingsPage', () => {
  it('opens Keycloak account console via active SSO session', async () => {
    const user = userEvent.setup();
    openKeycloakAccountConsole.mockClear();

    render(<SecuritySettingsPage />);

    await user.click(screen.getByRole('button', { name: /open account console/i }));

    expect(openKeycloakAccountConsole).toHaveBeenCalledWith(
      expect.objectContaining({
        createAccountUrl: expect.any(Function),
      }),
    );
  });
});
