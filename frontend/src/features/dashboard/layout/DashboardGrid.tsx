// frontend/src/features/dashboard/layout/DashboardGrid.tsx
import type { ReactNode } from 'react';

interface DashboardGridProps {
  children: ReactNode;
}

export function DashboardGrid({ children }: DashboardGridProps) {
  return <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{children}</div>;
}
