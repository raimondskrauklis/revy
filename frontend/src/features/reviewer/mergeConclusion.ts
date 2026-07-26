// frontend/src/features/reviewer/mergeConclusion.ts
import type { MergeConclusion, ReconciledFinding } from '@/features/reviewer/types';

/** Mirrors backend R6-Q2 `compute_check_conclusion` for active groups. */
export function deriveMergeConclusion(findings: ReconciledFinding[]): MergeConclusion {
  const active = findings.filter((item) => item.state === 'active');
  if (active.some((item) => item.severity === 'error' || item.severity === 'critical')) {
    return 'failure';
  }
  if (active.length === 0) {
    return 'success';
  }
  if (active.every((item) => item.severity === 'warning' || item.severity === 'info')) {
    return 'neutral';
  }
  return 'success';
}

export function pickLatestRevisionId(findings: ReconciledFinding[]): string | null {
  if (findings.length === 0) {
    return null;
  }
  return findings[0]?.last_seen_revision_id ?? null;
}
