// frontend/src/components/layout/MobileSidebarSheet.tsx
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSidebar } from '@/components/layout/SidebarProvider';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { acquireScrollLock, releaseScrollLock } from '@/lib/scrollLock';

function focusTrap(e: KeyboardEvent, container: HTMLElement): void {
  if (e.key !== 'Tab') return;
  const focusable = container.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  );
  if (focusable.length === 0) return;
  const first = focusable[0]!;
  const last = focusable[focusable.length - 1]!;
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}

export function MobileSidebarSheet() {
  const { state, closeMobile } = useSidebar();
  const { t } = useTranslation();
  const location = useLocation();
  const sheetRef = useRef<HTMLDivElement>(null);
  const isOpen = state === 'overlaid';

  // Close on route change
  useEffect(() => {
    if (isOpen) closeMobile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Close on Escape + focus trap on Tab
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeMobile();
        return;
      }
      if (sheetRef.current) focusTrap(e, sheetRef.current);
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
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