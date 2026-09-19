// frontend/src/features/reviewer/ReviewerSummaryWidget.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ReviewerSummaryWidget } from '@/features/reviewer/ReviewerSummaryWidget';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/reviewer/hooks', () => ({
  useReviewerAvailability: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { useReviewerAvailability } from '@/features/reviewer/hooks';

function renderWidget() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ReviewerSummaryWidget />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function activeUser(workspaceId: string | null) {
  return {
    user: {
      id: '1',
      email: 'admin@example.com',
      full_name: 'Admin',
      status: 'active',
      platform_role: null,
      workspace_id: workspaceId,
      role: AppRole.admin,
      memberships: [],
      locale: 'en',
      timezone: 'UTC',
    },
  } as unknown as ReturnType<typeof useAuth>;
}

describe('ReviewerSummaryWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows connect when reviewer is unavailable', () => {
    vi.mocked(useAuth).mockReturnValue(activeUser('ws-1'));
    vi.mocked(useReviewerAvailability).mockReturnValue({
      data: false,
      isLoading: false,
    } as unknown as ReturnType<typeof useReviewerAvailability>);

    renderWidget();

    expect(screen.getByText(/connect a github installation/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /connect github/i })).toHaveAttribute(
      'href',
      '/installations',
    );
    expect(screen.queryByRole('link', { name: /open reviewer/i })).not.toBeInTheDocument();
  });

  it('opens reviewer when available', () => {
    vi.mocked(useAuth).mockReturnValue(activeUser('ws-1'));
    vi.mocked(useReviewerAvailability).mockReturnValue({
      data: true,
      isLoading: false,
    } as unknown as ReturnType<typeof useReviewerAvailability>);

    renderWidget();

    expect(screen.getByRole('link', { name: /open reviewer/i })).toHaveAttribute(
      'href',
      '/reviewer',
    );
  });

  it('shows workspace copy without a connect CTA when no workspace', () => {
    vi.mocked(useAuth).mockReturnValue(activeUser(null));
    vi.mocked(useReviewerAvailability).mockReturnValue({
      data: false,
      isLoading: false,
    } as unknown as ReturnType<typeof useReviewerAvailability>);

    renderWidget();

    expect(screen.getByText(/select a workspace to use the reviewer/i)).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('hides the CTA while availability is loading', () => {
    vi.mocked(useAuth).mockReturnValue(activeUser('ws-1'));
    vi.mocked(useReviewerAvailability).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useReviewerAvailability>);

    renderWidget();

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
