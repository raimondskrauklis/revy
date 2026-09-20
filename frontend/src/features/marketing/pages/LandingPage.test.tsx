// frontend/src/features/marketing/pages/LandingPage.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LandingPage } from '@/features/marketing/pages/LandingPage';

const mockLogin = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('LandingPage', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      login: mockLogin,
    } as unknown as ReturnType<typeof useAuth>);
  });

  it('renders operator hero without feature cards', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /catch cut corners before they bite/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enter console/i })).toBeInTheDocument();
  });

  it('calls login on enter console click', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /enter console/i }));
    expect(mockLogin).toHaveBeenCalled();
  });

  it('replaces authenticated users to reviewer', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      login: mockLogin,
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