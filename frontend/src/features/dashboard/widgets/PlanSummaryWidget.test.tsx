// frontend/src/features/dashboard/widgets/PlanSummaryWidget.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { PlanSummaryWidget } from '@/features/dashboard/widgets/PlanSummaryWidget';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('PlanSummaryWidget', () => {
  it('shows current plan and billing link', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: 'pro',
        role: AppRole.admin,
        memberships: [],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <PlanSummaryWidget />
      </MemoryRouter>,
    );

    expect(screen.getByText(/pro/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /manage billing/i })).toHaveAttribute(
      'href',
      '/settings/billing',
    );
  });
});
