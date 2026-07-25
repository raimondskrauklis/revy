// frontend/src/features/admin/layout/AdminLayout.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AdminLayout } from '@/features/admin/layout/AdminLayout';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { email: 'admin@example.com', full_name: 'Admin', platform_role: 'super_admin' },
    logout: vi.fn(),
  }),
}));

describe('AdminLayout', () => {
  it('renders admin nav links', () => {
    render(
      <MemoryRouter initialEntries={['/admin/dashboard']}>
        <Routes>
          <Route path="/admin" element={<AdminLayout />}>
            <Route path="dashboard" element={<p>Dashboard content</p>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('navigation', { name: /admin sections/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^dashboard$/i })).toHaveAttribute(
      'href',
      '/admin/dashboard',
    );
    expect(screen.getByRole('link', { name: /^workspaces$/i })).toHaveAttribute(
      'href',
      '/admin/workspaces',
    );
    expect(screen.getByRole('link', { name: /^users$/i })).toHaveAttribute('href', '/admin/users');
    expect(screen.getByRole('link', { name: /^audit$/i })).toHaveAttribute('href', '/admin/audit');
    expect(screen.getByRole('link', { name: /^settings$/i })).toHaveAttribute(
      'href',
      '/admin/settings',
    );
  });
});
