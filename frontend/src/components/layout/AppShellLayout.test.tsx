// frontend/src/components/layout/AppShellLayout.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppShellLayout } from '@/components/layout/AppShellLayout';

const storage = new Map<string, string>();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    logout: vi.fn(),
  }),
}));

vi.mock('@/platform/extensions/hooks', () => ({
  useExtensions: () => [],
}));

describe('AppShellLayout', () => {
  beforeEach(() => {
    storage.clear();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
      clear: () => {
        storage.clear();
      },
    });
  });

  it('renders wordmark and radius token on nav, not rounded-xl', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/" element={<AppShellLayout />}>
            <Route path="dashboard" element={<p>Home</p>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('revy')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /revy/i })).toHaveAttribute('href', '/reviewer');
    const navHtml = container.querySelector('nav')?.innerHTML ?? '';
    expect(navHtml).toContain('--app-radius-md');
    expect(navHtml).not.toContain('rounded-xl');
  });
});