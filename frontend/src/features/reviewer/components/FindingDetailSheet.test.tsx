// frontend/src/features/reviewer/components/FindingDetailSheet.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';
import { FindingDetailSheet } from '@/features/reviewer/components/FindingDetailSheet';
import type { ReconciledFinding } from '@/features/reviewer/types';

const finding: ReconciledFinding = {
  id: 'f1',
  pull_request_id: 'pr1',
  severity: 'warning',
  category: 'bug',
  title: 'Cross-site scripting in user input',
  message: 'User input is rendered without escaping in the comment section.',
  file_path: 'src/app.ts',
  state: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_seen_revision_id: 'abc1234',
};

function renderSheet(overrides: Partial<Parameters<typeof FindingDetailSheet>[0]> = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FindingDetailSheet
        finding={finding}
        workspaceId="ws1"
        repoId="r1"
        prId="pr1"
        revisionId="abc1234"
        onClose={vi.fn()}
        canDismiss
        dismissPending={false}
        onDismiss={vi.fn()}
        {...overrides}
      />
    </QueryClientProvider>,
  );
}

describe('FindingDetailSheet', () => {
  it('renders finding title', () => {
    renderSheet();
    expect(screen.getByText('Cross-site scripting in user input')).toBeInTheDocument();
  });

  it('renders message', () => {
    renderSheet();
    expect(screen.getByText(/without escaping/)).toBeInTheDocument();
  });

  it('renders close button', () => {
    renderSheet();
    expect(screen.getByRole('button', { name: /close menu/i })).toBeInTheDocument();
  });

  it('calls onClose when backdrop clicked', () => {
    const onClose = vi.fn();
    renderSheet({ onClose });
    // Click the backdrop (first div with bg-black/40)
    const backdrop = document.querySelector('.bg-black\\/40');
    if (backdrop) fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose on Escape key', () => {
    const onClose = vi.fn();
    renderSheet({ onClose });
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('does not render dismiss button when cannot dismiss', () => {
    renderSheet({ canDismiss: false });
    expect(screen.queryByText(/Dismiss finding/i)).not.toBeInTheDocument();
  });

  it('renders dismiss button when can dismiss and finding is active', () => {
    renderSheet({ canDismiss: true });
    expect(screen.getByText(/Dismiss finding/i)).toBeInTheDocument();
  });

  it('does not render dismiss button for non-active finding', () => {
    renderSheet({
      finding: { ...finding, state: 'resolved' },
      canDismiss: true,
    });
    expect(screen.queryByText(/Dismiss finding/i)).not.toBeInTheDocument();
  });
});