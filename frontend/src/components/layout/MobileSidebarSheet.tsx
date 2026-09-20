// frontend/src/components/layout/MobileSidebarSheet.tsx
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useSidebar } from '@/components/layout/SidebarProvider';
import { AppSidebar } from '@/components/layout/AppSidebar';

export function MobileSidebarSheet() {
  const { state, closeMobile } = useSidebar();
  const location = useLocation();
  const backdropRef = useRef<HTMLDivElement>(null);
  const isOpen = state === 'overlaid';

  // Close on route change
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

  // Body scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      {/* Backdrop */}
      <div
        ref={backdropRef}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={closeMobile}
        aria-hidden
      />
      {/* Sheet */}
      <div className="absolute inset-y-0 left-0 w-[260px] bg-[color:var(--app-surface)] shadow-lg overflow-y-auto">
        <AppSidebar overlay />
      </div>
    </div>
  );
}