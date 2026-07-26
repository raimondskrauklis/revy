// frontend/src/features/marketing/pages/LandingPage.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { LandingPage } from '@/features/marketing/pages/LandingPage';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    isAuthenticated: false,
    isLoading: false,
  })),
}));

describe('LandingPage', () => {
  it('renders hero and sign-in links', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /ship with confidence/i })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /sign in/i }).length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: /get started/i })).toHaveAttribute('href', '/login');
  });
});
