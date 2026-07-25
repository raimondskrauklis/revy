// frontend/src/stores/themeStore.ts
import { create } from 'zustand';
import { applyTheme, getStoredTheme, type ThemeMode } from '@/lib/theme';

interface ThemeState {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  mode: 'system',
  setMode: (mode) => {
    applyTheme(mode);
    set({ mode });
  },
}));

export function initializeTheme(): void {
  const mode = getStoredTheme();
  applyTheme(mode);
  useThemeStore.setState({ mode });
}
