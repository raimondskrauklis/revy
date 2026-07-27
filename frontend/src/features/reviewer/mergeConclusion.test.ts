// frontend/src/features/reviewer/mergeConclusion.test.ts
import { describe, expect, it } from 'vitest';
import { deriveMergeConclusion, pickLatestRevisionId } from '@/features/reviewer/mergeConclusion';
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
  it('returns neutral when active critical finding exists', () => {
    expect(
      deriveMergeConclusion([finding({ severity: 'critical', state: 'active' })]),
    ).toBe('neutral');
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

  it('returns neutral for unknown active severity', () => {
    expect(
      deriveMergeConclusion([
        finding({ severity: 'bogus' as ReconciledFinding['severity'], state: 'active' }),
      ]),
    ).toBe('neutral');
  });
});

describe('pickLatestRevisionId', () => {
  it('picks revision from finding with latest updated_at', () => {
    const older = finding({
      severity: 'warning',
      state: 'active',
      last_seen_revision_id: 'rev-old',
      updated_at: '2026-01-01T00:00:00Z',
    });
    const newer = finding({
      severity: 'info',
      state: 'active',
      last_seen_revision_id: 'rev-new',
      updated_at: '2026-01-02T00:00:00Z',
    });
    expect(pickLatestRevisionId([older, newer])).toBe('rev-new');
  });
});
