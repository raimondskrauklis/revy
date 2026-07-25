// frontend/src/features/settings/layout/SettingsLayout.tsx
import { Outlet } from 'react-router-dom';
import { SettingsSidebar } from '@/features/settings/layout/SettingsSidebar';

export function SettingsLayout() {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6 md:flex-row">
      <SettingsSidebar />
      <div className="min-w-0 flex-1">
        <Outlet />
      </div>
    </div>
  );
}
