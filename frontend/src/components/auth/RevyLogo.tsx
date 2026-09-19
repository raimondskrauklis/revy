// frontend/src/components/auth/RevyLogo.tsx
import { Link } from 'react-router-dom';

interface RevyLogoProps {
  to?: string;
  className?: string;
  showWordmark?: boolean;
}

function WedgeMark() {
  return (
    <svg
      aria-hidden
      className="h-6 w-6 shrink-0 text-[color:var(--app-primary)]"
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M4 3.5 20 12 4 20.5V15.2L12.4 12 4 8.8V3.5Z" />
    </svg>
  );
}

export function RevyLogo({ to = '/', className = '', showWordmark = true }: RevyLogoProps) {
  const mark = (
    <span className={`inline-flex items-center gap-2 font-mono ${className}`}>
      <WedgeMark />
      {showWordmark ? (
        <span className="text-lg tracking-tight text-[color:var(--app-text-strong)]">revy</span>
      ) : null}
    </span>
  );

  if (to) {
    return (
      <Link
        to={to}
        className="inline-flex rounded-[var(--app-radius-md)] focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
      >
        {mark}
      </Link>
    );
  }

  return mark;
}
