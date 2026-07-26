// frontend/src/features/reviewer/ReviewerNavItem.tsx
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { GitPullRequest } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useReviewerAvailability } from '@/features/reviewer/hooks';

export function ReviewerNavItem() {
  const { t } = useTranslation();
  const location = useLocation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { data: available, isLoading } = useReviewerAvailability(workspaceId);

  if (isLoading || !available) {
    return null;
  }

  const active =
    location.pathname === '/reviewer' || location.pathname.startsWith('/reviewer/');

  return (
    <li>
      <Link
        to="/reviewer"
        className={[
          'flex min-h-11 items-center gap-2 rounded-lg px-3 py-2 text-sm',
          'focus-visible:ring-2 ring-[color:var(--app-ring-strong)]',
          active
            ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
            : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
        ].join(' ')}
      >
        <GitPullRequest className="h-4 w-4 shrink-0" aria-hidden />
        {t('nav.reviewer')}
      </Link>
    </li>
  );
}
