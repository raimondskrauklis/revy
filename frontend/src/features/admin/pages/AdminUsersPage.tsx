// frontend/src/features/admin/pages/AdminUsersPage.tsx
import { useTranslation } from 'react-i18next';

export function AdminUsersPage() {
  const { t } = useTranslation();
  return (
    <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.users.placeholder')}</p>
  );
}
