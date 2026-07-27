// frontend/src/features/reviewer/mergeConclusion.ts
import type { MergeConclusion, ReconciledFinding } from '@/features/reviewer/types';

/** Advisory merge signal — mirrors backend check conclusion (Greptile-class, not CI gate). */
export function deriveMergeConclusion(findings: ReconciledFinding[]): MergeConclusion {
  const active = findings.filter((item) => item.state === 'active');
  if (active.length === 0) {
    return 'success';
  }
  return 'neutral';
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
