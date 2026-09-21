// frontend/src/lib/scrollLock.ts
let lockCount = 0;

/** Increment body scroll lock. Call releaseScrollLock in cleanup. */
export function acquireScrollLock(): void {
  lockCount += 1;
  document.body.style.overflow = 'hidden';
}

/** Decrement body scroll lock — only restores scrolling when all locks are released. */
export function releaseScrollLock(): void {
  lockCount = Math.max(0, lockCount - 1);
  if (lockCount === 0) {
    document.body.style.overflow = '';
  }
}