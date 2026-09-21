// frontend/src/components/layout/MobileSidebarSheet.tsx
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSidebar } from '@/components/layout/SidebarProvider';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { acquireScrollLock, releaseScrollLock } from '@/lib/scrollLock';

export function MobileSidebarSheet() {
  const { state, closeMobile } = useSidebar();
  const { t } = useTranslation();
  const location = useLocation();
  const sheetRef = useRef<HTMLDivElement>(null);
  const isOpen = state === 'overlaid';

  // Focus trap + close on route change
  useEffect(() => {
    if (isOpen) closeMobile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeMobile();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeMobile]);

  // Body scroll lock (ref-counted)
  useEffect(() => {
    if (isOpen) {
      acquireScrollLock();
      return () => releaseScrollLock();
    }
  }, [isOpen]);

  // Focus the sheet panel when opened
  useEffect(() => {
    if (isOpen && sheetRef.current) {
      sheetRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={closeMobile}
        aria-hidden
      />
      {/* Sheet */}
      <div
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-label={t('sidebar.mainNav')}
        className="absolute inset-y-0 left-0 w-[260px] bg-[color:var(--app-surface)] shadow-lg overflow-y-auto outline-none"
        tabIndex={-1}
      >
        <AppSidebar overlay />
      </div>
    </div>
  );
}