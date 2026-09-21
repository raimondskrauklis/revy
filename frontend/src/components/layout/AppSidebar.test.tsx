// frontend/src/components/layout/AppSidebar.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { SidebarProvider } from '@/components/layout/SidebarProvider';

const storage = new Map<string, string>();

function renderSidebar(initialEntries: string[] = ['/dashboard']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <SidebarProvider>
        <AppSidebar />
      </SidebarProvider>
    </MemoryRouter>,
  );
}

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

describe('AppSidebar', () => {
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

  it('renders wordmark', () => {
    renderSidebar();
    expect(screen.getByText('revy')).toBeInTheDocument();
  });

  it('renders nav aria-label', () => {
    renderSidebar();
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument();
  });

  it('renders collapse toggle button', () => {
    renderSidebar();
    expect(screen.getByRole('button', { name: /collapse sidebar/i })).toBeInTheDocument();
  });

  it('renders wordmark link pointing to reviewer', () => {
    renderSidebar();
    expect(screen.getByRole('link', { name: /revy/i })).toHaveAttribute('href', '/reviewer');
  });

  it('renders Settings accordion button', () => {
    renderSidebar();
    expect(screen.getByRole('button', { name: /Settings/i })).toBeInTheDocument();
  });

  it('expands Settings accordion on click', () => {
    renderSidebar();
    const settingsBtn = screen.getByRole('button', { name: /Settings/i });
    act(() => {
      fireEvent.click(settingsBtn);
    });
    // After expanding, Personal group label appears
    expect(screen.getByText(/Personal/i)).toBeInTheDocument();
  });

  it('auto-opens Settings accordion when on settings page', () => {
    renderSidebar(['/settings/profile']);
    // Settings accordion should be open by default on settings pages
    expect(screen.getByText(/Personal/i)).toBeInTheDocument();
  });
});