// frontend/src/features/auth/pages/LoginPage.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { LoginPage } from '@/features/auth/pages/LoginPage';

const login = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    isAuthenticated: false,
    isLoading: false,
    login,
  })),
}));

describe('LoginPage', () => {
  it('renders SSO button and triggers login', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(container.querySelector('.lg\\:grid-cols-2')).not.toBeNull();

    const button = screen.getByRole('button', { name: /continue with sso/i });
    expect(button).toBeInTheDocument();
    await user.click(button);
    expect(login).toHaveBeenCalledWith('/reviewer');
  });
});
