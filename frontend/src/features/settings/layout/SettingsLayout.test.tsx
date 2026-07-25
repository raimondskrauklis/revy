// frontend/src/features/settings/layout/SettingsLayout.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SettingsLayout } from '@/features/settings/layout/SettingsLayout';
import { ProfileSettingsPage } from '@/features/settings/pages/ProfileSettingsPage';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ user: null, refetchUser: vi.fn() }),
}));

describe('SettingsLayout', () => {
  it('renders personal nav links and workspace group label only', () => {
    render(
      <MemoryRouter initialEntries={['/settings/profile']}>
        <Routes>
          <Route path="/settings" element={<SettingsLayout />}>
            <Route path="profile" element={<ProfileSettingsPage />} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('navigation', { name: /settings sections/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^profile$/i })).toHaveAttribute(
      'href',
      '/settings/profile',
    );
    expect(screen.getByRole('link', { name: /^security$/i })).toHaveAttribute(
      'href',
      '/settings/security',
    );
    expect(screen.getByRole('link', { name: /^appearance$/i })).toHaveAttribute(
      'href',
      '/settings/appearance',
    );
    expect(screen.getByText('Workspace')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /workspace/i })).not.toBeInTheDocument();
  });
});
