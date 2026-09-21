// frontend/src/lib/scrollLock.ts
let lockCount = 0;

/** Find the app scroll container (the overflow-y-auto child of the main layout). */
function getScrollContainer(): HTMLElement | null {
  return document.querySelector('[data-scroll-lock-target]')
    ?? document.querySelector('#app-content [class*="overflow-y-auto"]');
}

/** Acquire body scroll lock. Call releaseScrollLock in cleanup. */
export function acquireScrollLock(): void {
  lockCount += 1;
  const target = getScrollContainer();
  if (target) target.style.overflow = 'hidden';
}

/** Release body scroll lock — only restores scrolling when all locks are released. */
export function releaseScrollLock(): void {
  lockCount = Math.max(0, lockCount - 1);
  if (lockCount === 0) {
    const target = getScrollContainer();
    if (target) target.style.overflow = '';
  }
}