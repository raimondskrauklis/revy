// frontend/src/features/reviewer/components/FindingsSummaryBar.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FindingsSummaryBar } from '@/features/reviewer/components/FindingsSummaryBar';
import type { ReconciledFinding } from '@/features/reviewer/types';

function f(overrides: Partial<ReconciledFinding>): ReconciledFinding {
  return {
    id: '1',
    pull_request_id: 'pr',
    category: 'bug',
    title: 'Test',
    message: 'm',
    file_path: null,
    last_seen_revision_id: 'rev',
    severity: 'warning',
    state: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('FindingsSummaryBar', () => {
  it('shows no findings message when empty', () => {
    render(<FindingsSummaryBar findings={[]} conclusion="success" />);
    expect(screen.getByText(/No findings/i)).toBeInTheDocument();
  });

  it('shows severity counts', () => {
    render(
      <FindingsSummaryBar
        findings={[
          f({ severity: 'critical', state: 'active' }),
          f({ severity: 'error', state: 'active' }),
          f({ severity: 'warning', state: 'active' }),
          f({ severity: 'info', state: 'active' }),
        ]}
        conclusion="failure"
      />,
    );
    expect(screen.getByText(/1 Critical/i)).toBeInTheDocument();
    expect(screen.getByText(/1 Error/i)).toBeInTheDocument();
    expect(screen.getByText(/1 Warning/i)).toBeInTheDocument();
    expect(screen.getByText(/1 Info/i)).toBeInTheDocument();
  });

  it('shows dismissed count', () => {
    render(
      <FindingsSummaryBar
        findings={[
          f({ severity: 'warning', state: 'resolved' }),
          f({ severity: 'warning', state: 'superseded' }),
        ]}
        conclusion="neutral"
      />,
    );
    expect(screen.getByText(/dismissed/i)).toBeInTheDocument();
  });

  it('shows blocked next action', () => {
    render(
      <FindingsSummaryBar
        findings={[f({ severity: 'critical', state: 'active' })]}
        conclusion="failure"
      />,
    );
    expect(screen.getByText(/Blocked/i)).toBeInTheDocument();
  });

  it('shows needs review next action', () => {
    render(
      <FindingsSummaryBar
        findings={[f({ severity: 'warning', state: 'active' })]}
        conclusion="neutral"
      />,
    );
    expect(screen.getByText(/Needs review/i)).toBeInTheDocument();
  });

  it('shows ready next action', () => {
    render(
      <FindingsSummaryBar
        findings={[f({ severity: 'info', state: 'resolved' })]}
        conclusion="success"
      />,
    );
    expect(screen.getByText(/Ready to merge/i)).toBeInTheDocument();
  });
});