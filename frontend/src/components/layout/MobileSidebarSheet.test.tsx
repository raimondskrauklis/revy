// frontend/src/components/layout/MobileSidebarSheet.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MobileSidebarSheet } from '@/components/layout/MobileSidebarSheet';
import { SidebarProvider, useSidebar } from '@/components/layout/SidebarProvider';

const storage = new Map<string, string>();

function TestHarness() {
  const { openMobile, state } = useSidebar();
  return (
    <div>
      <button data-testid="trigger" onClick={openMobile}>Open</button>
      <span data-testid="state">{state}</span>
      <MobileSidebarSheet />
    </div>
  );
}

function renderSheet() {
  return render(
    <MemoryRouter>
      <SidebarProvider>
        <TestHarness />
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

describe('MobileSidebarSheet', () => {
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

  it('is hidden when not overlaid', () => {
    renderSheet();
    expect(screen.queryByRole('button', { name: /collapse sidebar/i })).not.toBeInTheDocument();
  });

  it('shows sidebar when overlaid', () => {
    renderSheet();
    act(() => {
      fireEvent.click(screen.getByTestId('trigger'));
    });
    // Sidebar content should be visible
    expect(screen.getByText('revy')).toBeInTheDocument();
  });

  it('closes on Escape key', () => {
    renderSheet();
    act(() => {
      fireEvent.click(screen.getByTestId('trigger'));
    });
    expect(screen.getByText('revy')).toBeInTheDocument();

    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    // After closing, sidebar content goes away
    expect(screen.queryByText('revy')).not.toBeInTheDocument();
  });
});