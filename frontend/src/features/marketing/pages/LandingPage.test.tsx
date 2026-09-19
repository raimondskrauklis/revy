// frontend/src/features/marketing/pages/LandingPage.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LandingPage } from '@/features/marketing/pages/LandingPage';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('LandingPage', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    } as unknown as ReturnType<typeof useAuth>);
  });

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

  it('replaces authenticated users to reviewer', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/reviewer" element={<div>Reviewer</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Reviewer')).toBeInTheDocument();
  });
});
