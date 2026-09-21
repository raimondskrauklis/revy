// frontend/src/components/layout/MobileBottomNav.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { MobileBottomNav } from '@/components/layout/MobileBottomNav';

describe('MobileBottomNav', () => {
  it('renders all 4 tabs', () => {
    render(
      <MemoryRouter>
        <MobileBottomNav />
      </MemoryRouter>,
    );
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Reviewer')).toBeInTheDocument();
    expect(screen.getByText('Installations')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders link to dashboard', () => {
    render(
      <MemoryRouter>
        <MobileBottomNav />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: /dashboard/i })).toHaveAttribute('href', '/dashboard');
  });

  it('renders link to settings', () => {
    render(
      <MemoryRouter>
        <MobileBottomNav />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: /settings/i })).toHaveAttribute('href', '/settings');
  });
});