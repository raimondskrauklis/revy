// frontend/src/lib/theme.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { applyTheme, getStoredTheme } from '@/lib/theme';

const storage = new Map<string, string>();

describe('applyTheme force-dark', () => {
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
    });
    document.documentElement.classList.remove('dark');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('paints html.dark for light and system', () => {
    applyTheme('light');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(getStoredTheme()).toBe('light');

    document.documentElement.classList.remove('dark');
    applyTheme('system');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(getStoredTheme()).toBe('system');
  });

  it('paints html.dark for dark', () => {
    applyTheme('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(getStoredTheme()).toBe('dark');
  });
});
