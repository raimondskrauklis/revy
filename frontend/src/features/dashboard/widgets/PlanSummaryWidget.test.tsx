// frontend/src/features/dashboard/widgets/PlanSummaryWidget.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PlanSummaryWidget } from '@/features/dashboard/widgets/PlanSummaryWidget';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

function makeUser(overrides: Record<string, unknown> = {}) {
  return {
    user: {
      id: '1',
      email: 'admin@example.com',
      full_name: 'Admin',
      status: 'active',
      platform_role: null,
      workspace_id: 'ws-1',
      workspace_plan: 'free',
      role: 'admin' as const,
      memberships: [],
      locale: 'en',
      timezone: 'UTC',
      completed_review_runs: 3,
      review_run_limit: 25,
      ...overrides,
    },
  } as unknown as ReturnType<typeof useAuth>;
}

describe('PlanSummaryWidget', () => {
  it('shows free plan with review run info', () => {
    vi.mocked(useAuth).mockReturnValue(makeUser());

    render(<PlanSummaryWidget />);

    expect(screen.getByText(/free/i)).toBeInTheDocument();
    expect(screen.getByText(/3\/25/i)).toBeInTheDocument();
  });

  it('shows feedback hint when under limit', () => {
    vi.mocked(useAuth).mockReturnValue(makeUser({ completed_review_runs: 5 }));

    render(<PlanSummaryWidget />);
    expect(screen.getByText(/feedback/i)).toBeInTheDocument();
  });

  it('does not show feedback hint when limit reached', () => {
    vi.mocked(useAuth).mockReturnValue(makeUser({ completed_review_runs: 25 }));
    render(<PlanSummaryWidget />);
    expect(screen.queryByText(/feedback/i)).not.toBeInTheDocument();
  });

  it('renders nothing without workspace', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
    } as unknown as ReturnType<typeof useAuth>);

    const { container } = render(<PlanSummaryWidget />);
    expect(container.firstChild).toBeNull();
  });
});