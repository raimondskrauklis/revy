// frontend/src/features/reviewer/components/FindingRow.test.tsx
import { fireEvent, render, screen } from '@testing-library/react';
import { FindingRow } from '@/features/reviewer/components/FindingRow';
import type { ReconciledFinding } from '@/features/reviewer/types';

const baseFinding: ReconciledFinding = {
  id: 'group-1',
  pull_request_id: 'pr-1',
  state: 'active',
  severity: 'warning',
  category: 'bug',
  title: 'Unused import',
  message: 'Remove unused import',
  file_path: 'app/main.ts',
  last_seen_revision_id: 'rev-1',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('FindingRow', () => {
  it('renders resolution method badge', () => {
    render(
      <table>
        <tbody>
          <FindingRow
            finding={{
              ...baseFinding,
              state: 'resolved',
              resolution_method: 'human_dismissed',
            }}
          />
        </tbody>
      </table>,
    );
    expect(screen.getByText('Dismissed by admin')).toBeInTheDocument();
  });

  it('shows dismiss action for active findings when admin', () => {
    const onDismiss = vi.fn();
    render(
      <table>
        <tbody>
          <FindingRow finding={baseFinding} canDismiss onDismiss={onDismiss} />
        </tbody>
      </table>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }));
    expect(onDismiss).toHaveBeenCalledWith('group-1');
  });

  it('hides dismiss for resolved findings', () => {
    render(
      <table>
        <tbody>
          <FindingRow
            finding={{ ...baseFinding, state: 'resolved', resolution_method: 'judge_dismissed' }}
            canDismiss
            onDismiss={vi.fn()}
          />
        </tbody>
      </table>,
    );
    expect(screen.queryByRole('button', { name: 'Dismiss' })).not.toBeInTheDocument();
  });
});
