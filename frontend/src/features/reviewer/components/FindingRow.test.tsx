// frontend/src/features/reviewer/components/FindingRow.test.tsx
import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';
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
  it.each([
    ['info', 'Info'],
    ['warning', 'Warning'],
    ['error', 'Error'],
    ['critical', 'Critical'],
  ] as const)('renders %s severity label and shape', (severity, label) => {
    const { container } = render(
      <table>
        <tbody>
          <FindingRow finding={{ ...baseFinding, severity }} />
        </tbody>
      </table>,
    );
    expect(screen.getByText(label)).toBeInTheDocument();
    expect(container.querySelector(`[data-severity-shape="${severity}"]`)).not.toBeNull();
  });

  it('truncates long finding messages', () => {
    const message = `${'word '.repeat(80)}end`;
    render(
      <table>
        <tbody>
          <FindingRow finding={{ ...baseFinding, message }} />
        </tbody>
      </table>,
    );
    const cell = screen.getByTitle(message);
    expect(cell).toHaveClass('truncate');
    expect(cell).toHaveClass('font-sans');
  });

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
