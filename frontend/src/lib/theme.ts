// frontend/src/lib/theme.ts
export type ThemeMode = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'app-theme';

export function getStoredTheme(): ThemeMode {
  if (typeof localStorage?.getItem !== 'function') {
    return 'system';
  }
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored;
  }
  return 'system';
}

/** Kept for console-only revert plumbing. Do not call for DOM paint — `applyTheme` always sets `html.dark`. */
export function resolveDarkMode(mode: ThemeMode): boolean {
  if (mode === 'dark') return true;
  if (mode === 'light') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function applyTheme(mode: ThemeMode): void {
  if (typeof localStorage?.setItem === 'function') {
    localStorage.setItem(STORAGE_KEY, mode);
  }
  if (typeof document !== 'undefined') {
    document.documentElement.classList.add('dark');
  }
}
