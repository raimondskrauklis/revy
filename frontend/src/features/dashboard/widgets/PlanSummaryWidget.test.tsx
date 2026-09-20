// frontend/src/features/dashboard/widgets/PlanSummaryWidget.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PlanSummaryWidget } from '@/features/dashboard/widgets/PlanSummaryWidget';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('PlanSummaryWidget', () => {
  it('shows free plan with review run info', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: 'free',
        role: AppRole.admin,
        memberships: [],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    render(<PlanSummaryWidget />);

    expect(screen.getByText(/free/i)).toBeInTheDocument();
    expect(screen.getByText(/25/i)).toBeInTheDocument();
  });

  it('renders nothing without workspace', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
    } as unknown as ReturnType<typeof useAuth>);

    const { container } = render(<PlanSummaryWidget />);
    expect(container.firstChild).toBeNull();
  });
});