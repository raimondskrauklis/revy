// frontend/src/components/auth/RevyLogo.tsx
import { Link } from 'react-router-dom';

interface RevyLogoProps {
  to?: string;
  className?: string;
  showWordmark?: boolean;
}

export function RevyLogo({ to = '/', className = '', showWordmark = true }: RevyLogoProps) {
  const mark = (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span
        aria-hidden
        className="flex h-9 w-9 items-center justify-center rounded-lg bg-[color:var(--app-cta-bg)] text-sm font-bold text-[color:var(--app-cta-fg)] shadow-sm"
      >
        R
      </span>
      {showWordmark ? (
        <span className="text-lg font-semibold tracking-tight text-[color:var(--app-text-strong)]">
          Revy
        </span>
      ) : null}
    </span>
  );

  if (to) {
    return (
      <Link to={to} className="inline-flex rounded-md focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]">
        {mark}
      </Link>
    );
  }

  return mark;
}
