// frontend/src/components/layout/WorkspaceSwitcher.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronsUpDown } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { setActiveWorkspace } from '@/lib/me';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function WorkspaceSwitcher() {
  const { t } = useTranslation();
  const { user, refetchUser } = useAuth();
  const [open, setOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  if (!user) {
    return null;
  }

  const memberships = user.memberships;
  if (memberships.length === 0) {
    return null;
  }

  const active = user.workspace_id
    ? memberships.find((m) => m.workspace_id === user.workspace_id)
    : undefined;
  const label = active?.workspace_name ?? t('header.workspace.select');

  const handleSwitch = async (workspaceId: string) => {
    if (workspaceId === user.workspace_id || switching) {
      setOpen(false);
      return;
    }
    setSwitching(true);
    try {
      await setActiveWorkspace(workspaceId);
      await refetchUser();
      setOpen(false);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setSwitching(false);
    }
  };

  if (memberships.length <= 1 && active) {
    return (
      <span className="truncate text-sm font-medium text-[color:var(--app-text-strong)]">
        {label}
      </span>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="flex max-w-[12rem] items-center gap-1 rounded-lg px-2 py-1.5 text-sm font-medium text-[color:var(--app-text-strong)] hover:bg-[color:var(--app-chip)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          aria-label={t('header.workspace.switch')}
          disabled={switching}
        >
          <span className="truncate">{label}</span>
          <ChevronsUpDown className="h-4 w-4 shrink-0 text-[color:var(--app-text-muted)]" aria-hidden />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-1" align="start">
        <ul role="listbox" aria-label={t('header.workspace.list')}>
          {memberships.map((membership) => {
            const selected = membership.workspace_id === user.workspace_id;
            return (
              <li key={membership.workspace_id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  className={[
                    'flex w-full rounded-lg px-3 py-2 text-left text-sm',
                    selected
                      ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
                      : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
                  ].join(' ')}
                  onClick={() => void handleSwitch(membership.workspace_id)}
                  disabled={switching}
                >
                  <span className="truncate">{membership.workspace_name}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
