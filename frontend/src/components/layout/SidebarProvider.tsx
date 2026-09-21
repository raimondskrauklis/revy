// frontend/src/components/layout/SidebarProvider.tsx
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

type SidebarState = 'expanded' | 'collapsed' | 'overlaid';

interface SidebarContextValue {
  state: SidebarState;
  toggle: () => void;
  expand: () => void;
  collapse: () => void;
  openMobile: () => void;
  closeMobile: () => void;
}

const STORAGE_KEY = 'app-sidebar-collapsed';
const MOBILE_MQ = '(max-width: 1023px)';

const SidebarContext = createContext<SidebarContextValue | null>(null);

function readInitialState(): SidebarState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'true') return 'collapsed';
  } catch {
    // localStorage unavailable — use matchMedia fallback
  }

  try {
    if (window.matchMedia(MOBILE_MQ).matches) return 'overlaid';
  } catch {
    // matchMedia unavailable — default
  }

  return 'expanded';
}

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SidebarState>(readInitialState);

  const toggle = useCallback(() => {
    setState((prev) => {
      if (prev === 'overlaid') return prev;
      const next = prev === 'expanded' ? 'collapsed' : 'expanded';
      localStorage.setItem(STORAGE_KEY, next === 'collapsed' ? 'true' : 'false');
      return next;
    });
  }, []);

  const expand = useCallback(() => {
    setState('expanded');
    localStorage.setItem(STORAGE_KEY, 'false');
  }, []);

  const collapse = useCallback(() => {
    setState('collapsed');
    localStorage.setItem(STORAGE_KEY, 'true');
  }, []);

  const openMobile = useCallback(() => {
    setState('overlaid');
  }, []);

  const closeMobile = useCallback(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    setState(stored === 'true' ? 'collapsed' : 'expanded');
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        // Don't toggle inside text inputs / contentEditable
        const tag = (e.target as HTMLElement)?.tagName ?? '';
        if (tag === 'INPUT' || tag === 'TEXTAREA' || (e.target as HTMLElement)?.isContentEditable) {
          return;
        }
        e.preventDefault();
        toggle();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggle]);

  const value = useMemo<SidebarContextValue>(
    () => ({ state, toggle, expand, collapse, openMobile, closeMobile }),
    [state, toggle, expand, collapse, openMobile, closeMobile],
  );

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;
}

export function useSidebar(): SidebarContextValue {
  const ctx = useContext(SidebarContext);
  if (!ctx) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return ctx;
}