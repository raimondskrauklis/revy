// frontend/src/components/layout/UserMenu.tsx
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LogOut, Shield, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { isPlatformAdmin } from '@/lib/permissions';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

function displayName(email: string, fullName: string | null): string {
  return fullName?.trim() || email;
}

export function UserMenu() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user) {
    return null;
  }

  const name = displayName(user.email, user.full_name);
  const showAdminLink = isPlatformAdmin(user.platform_role ?? undefined);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="flex max-w-[10rem] items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-[color:var(--app-text-strong)] hover:bg-[color:var(--app-chip)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          aria-label={t('header.user.menu')}
        >
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[color:var(--app-chip)] text-xs font-semibold">
            {name.charAt(0).toUpperCase()}
          </span>
          <span className="hidden truncate sm:inline">{name}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-52 p-1" align="end">
        <div className="border-b border-[color:var(--app-ring)] px-3 py-2">
          <p className="truncate text-sm font-medium text-[color:var(--app-text-strong)]">{name}</p>
          <p className="truncate text-xs text-[color:var(--app-text-muted)]">{user.email}</p>
        </div>
        <ul className="py-1">
          {showAdminLink ? (
            <li>
              <Link
                to="/admin"
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]"
                onClick={() => setOpen(false)}
              >
                <Shield className="h-4 w-4" aria-hidden />
                {t('header.user.admin')}
              </Link>
            </li>
          ) : null}
          <li>
            <Link
              to="/settings/profile"
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]"
              onClick={() => setOpen(false)}
            >
              <User className="h-4 w-4" aria-hidden />
              {t('header.user.profile')}
            </Link>
          </li>
          <li>
            <button
              type="button"
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]"
              onClick={() => {
                setOpen(false);
                logout();
              }}
            >
              <LogOut className="h-4 w-4" aria-hidden />
              {t('header.user.signOut')}
            </button>
          </li>
        </ul>
      </PopoverContent>
    </Popover>
  );
}
