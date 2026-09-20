// frontend/src/components/layout/AppHeader.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppHeader } from '@/components/layout/AppHeader';
import { SidebarProvider } from '@/components/layout/SidebarProvider';

const storage = new Map<string, string>();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    logout: vi.fn(),
  }),
}));

function renderHeader() {
  return render(
    <MemoryRouter>
      <SidebarProvider>
        <AppHeader />
      </SidebarProvider>
    </MemoryRouter>,
  );
}

describe('AppHeader', () => {
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

  it('renders hamburger button on mobile header', () => {
    renderHeader();
    expect(screen.getByRole('button', { name: /open navigation menu/i })).toBeInTheDocument();
  });
});