// frontend/src/features/settings/pages/AppearanceSettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppearanceSettingsPage } from '@/features/settings/pages/AppearanceSettingsPage';
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

describe('AppearanceSettingsPage', () => {
  beforeEach(() => {
    storage.clear();
    mockLocalStorage();
    document.documentElement.classList.remove('dark');
    initializeTheme();
  });

  it('renders theme selector bound to theme store', () => {
    render(<AppearanceSettingsPage />);

    expect(screen.getByRole('heading', { name: /appearance/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /theme/i })).toBeInTheDocument();

    useThemeStore.getState().setMode('dark');
    expect(useThemeStore.getState().mode).toBe('dark');
    expect(storage.get('app-theme')).toBe('dark');
  });
});
