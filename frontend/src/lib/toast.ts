// frontend/src/lib/toast.ts
/**
 * Toast utility — Sonner wrapper with platform defaults (duration, richColors).
 *
 * **features/** — prefer this for success / info / warning / neutral feedback.
 * API / domain failures → `showDomainErrorToast` / `notify` (@/shared/errors/toasts).
 *
 * Direct `import { toast } from 'sonner'` in features: escape hatch only when this
 * wrapper lacks an API (custom JSX, action buttons, dismiss by id). Extend here first.
 *
 * Infrastructure (`lib/*`, `shared/errors/*`, `main.tsx`) may import sonner — see
 * docs/errors/OBSERVABILITY.md §6.
 */
import { toast as sonnerToast } from 'sonner';

const defaults = { richColors: true as const };

export const toast = {
  success(message: string, description?: string) {
    sonnerToast.success(message, { description, duration: 3000, ...defaults });
  },
  error(message: string, description?: string) {
    sonnerToast.error(message, { description, duration: Infinity, ...defaults });
  },
  warning(message: string, description?: string) {
    sonnerToast.warning(message, { description, duration: 5000, ...defaults });
  },
  info(message: string, description?: string) {
    sonnerToast.info(message, { description, duration: 3000, ...defaults });
  },
  /** Neutral toast — no success/error icon (Sonner `toast.message`). */
  message(message: string, description?: string) {
    sonnerToast.message(message, { description, duration: 3000, ...defaults });
  },
  dismiss: sonnerToast.dismiss,
};
