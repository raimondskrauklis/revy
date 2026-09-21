// frontend/src/features/reviewer/mergeConclusion.ts
import type { MergeConclusion, ReconciledFinding } from '@/features/reviewer/types';

/** Advisory merge signal — tiered: Critical/Error → blocked, Warning only → needs review, none → ready. */
export function deriveMergeConclusion(findings: ReconciledFinding[]): MergeConclusion {
  const active = findings.filter((item) => item.state === 'active');
  if (active.length === 0) {
    return 'success';
  }

  const hasBlocking = active.some(
    (f) => f.severity === 'critical' || f.severity === 'error',
  );
  if (hasBlocking) {
    return 'failure';
  }

  const hasWarning = active.some((f) => f.severity === 'warning');
  if (hasWarning) {
    return 'neutral';
  }

  const hasInfo = active.some((f) => f.severity === 'info');
  // Only info findings active — treat as success (no warnings or above); unknown → neutral
  return hasInfo ? 'success' : 'neutral';
}

export function pickLatestRevisionId(findings: ReconciledFinding[]): string | null {
  if (findings.length === 0) {
    return null;
  }
  let latest = findings[0]!;
  for (const item of findings.slice(1)) {
    if (item.updated_at > latest.updated_at) {
      latest = item;
    }
  }
  return latest.last_seen_revision_id;
}