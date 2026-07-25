// frontend/src/stores/themeStore.test.ts
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useThemeStore, initializeTheme } from '@/stores/themeStore';

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
  });
}

describe('themeStore', () => {
  beforeEach(() => {
    storage.clear();
    mockLocalStorage();
    document.documentElement.classList.remove('dark');
    initializeTheme();
  });

  it('persists dark theme to localStorage and html class', () => {
    useThemeStore.getState().setMode('dark');

    expect(localStorage.getItem('app-theme')).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(useThemeStore.getState().mode).toBe('dark');
  });

  it('removes dark class for light theme', () => {
    document.documentElement.classList.add('dark');
    useThemeStore.getState().setMode('light');

    expect(localStorage.getItem('app-theme')).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});
