// frontend/src/features/reviewer/mergeConclusion.test.ts
import { describe, expect, it } from 'vitest';
import { deriveMergeConclusion } from '@/features/reviewer/mergeConclusion';
import type { ReconciledFinding } from '@/features/reviewer/types';

function finding(
  overrides: Partial<ReconciledFinding> & Pick<ReconciledFinding, 'severity' | 'state'>,
): ReconciledFinding {
  return {
    id: '1',
    pull_request_id: 'pr',
    category: 'bug',
    title: 't',
    message: 'm',
    file_path: null,
    last_seen_revision_id: 'rev',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('deriveMergeConclusion', () => {
  it('returns failure when active critical finding exists', () => {
    expect(
      deriveMergeConclusion([finding({ severity: 'critical', state: 'active' })]),
    ).toBe('failure');
  });

  it('returns neutral when only warnings remain active', () => {
    expect(
      deriveMergeConclusion([finding({ severity: 'warning', state: 'active' })]),
    ).toBe('neutral');
  });

  it('returns success when no active findings', () => {
    expect(
      deriveMergeConclusion([finding({ severity: 'error', state: 'resolved' })]),
    ).toBe('success');
  });
});
