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
  it('renders operator hero without feature cards', () => {
    const { container } = render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /findings before you merge/i })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /sign in/i }).length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: /open console/i })).toHaveAttribute('href', '/login');
    expect(container.querySelector('svg.lucide')).toBeNull();
    expect(screen.queryByRole('heading', { name: /github-native/i })).not.toBeInTheDocument();
  });
});
