// frontend/src/features/reviewer/pullRequestLifecycle.test.ts
import { describe, expect, it } from 'vitest';
import { pullRequestLifecycle } from '@/features/reviewer/pullRequestLifecycle';

describe('pullRequestLifecycle', () => {
  it('returns merged when GitHub merged flag is set', () => {
    expect(pullRequestLifecycle({ state: 'closed', merged: true })).toBe('merged');
  });

  it('returns closed when closed without merge', () => {
    expect(pullRequestLifecycle({ state: 'closed', merged: false })).toBe('closed');
  });

  it('returns open for an open pull request', () => {
    expect(pullRequestLifecycle({ state: 'open', merged: false })).toBe('open');
  });
});
