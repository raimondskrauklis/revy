// frontend/src/components/layout/SidebarProvider.test.tsx
import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SidebarProvider, useSidebar } from '@/components/layout/SidebarProvider';

const storage = new Map<string, string>();

function mockLocalStorage() {
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
}

function makeWrapper() {
  return ({ children }: { children: React.ReactNode }) => (
    <SidebarProvider>{children}</SidebarProvider>
  );
}

describe('SidebarProvider', () => {
  beforeEach(() => {
    storage.clear();
    mockLocalStorage();
  });

  it('provides sidebar context with default state', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });
    expect(['expanded', 'collapsed', 'overlaid']).toContain(result.current.state);
  });

  it('toggle switches between expanded and collapsed', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.expand());
    expect(result.current.state).toBe('expanded');

    act(() => result.current.toggle());
    expect(result.current.state).toBe('collapsed');

    act(() => result.current.toggle());
    expect(result.current.state).toBe('expanded');
  });

  it('toggle on overlaid expands the sidebar', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.openMobile());
    expect(result.current.state).toBe('overlaid');

    act(() => result.current.toggle());
    expect(result.current.state).toBe('expanded');
  });

  it('expand sets expanded state', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.collapse());
    expect(result.current.state).toBe('collapsed');

    act(() => result.current.expand());
    expect(result.current.state).toBe('expanded');
  });

  it('collapse sets collapsed state', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.expand());
    expect(result.current.state).toBe('expanded');

    act(() => result.current.collapse());
    expect(result.current.state).toBe('collapsed');
  });

  it('openMobile sets overlaid state', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.openMobile());
    expect(result.current.state).toBe('overlaid');
  });

  it('closeMobile resets to expanded', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.openMobile());
    expect(result.current.state).toBe('overlaid');

    act(() => result.current.closeMobile());
    expect(result.current.state).toBe('expanded');
  });

  it('persists collapsed state to localStorage', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.collapse());
    expect(localStorage.getItem('app-sidebar-collapsed')).toBe('true');

    act(() => result.current.expand());
    expect(localStorage.getItem('app-sidebar-collapsed')).toBe('false');
  });

  it('closeMobile preserves collapse preference', () => {
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });

    act(() => result.current.collapse());
    expect(localStorage.getItem('app-sidebar-collapsed')).toBe('true');

    act(() => result.current.openMobile());
    act(() => result.current.closeMobile());
    // closeMobile respects user's previous collapse preference
    expect(result.current.state).toBe('collapsed');
    expect(localStorage.getItem('app-sidebar-collapsed')).toBe('true');
  });

  it('throws when used outside provider', () => {
    expect(() => renderHook(() => useSidebar())).toThrow(
      'useSidebar must be used within a SidebarProvider',
    );
  });

  it('reads collapsed initial state from localStorage', () => {
    storage.set('app-sidebar-collapsed', 'true');
    const { result } = renderHook(() => useSidebar(), { wrapper: makeWrapper() });
    expect(result.current.state).toBe('collapsed');
  });
});