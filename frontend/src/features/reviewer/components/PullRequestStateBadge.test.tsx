// frontend/src/features/reviewer/components/PullRequestStateBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PullRequestStateBadge } from '@/features/reviewer/components/PullRequestStateBadge';

describe('PullRequestStateBadge', () => {
  it('shows merged for a merged pull request', () => {
    render(<PullRequestStateBadge pullRequest={{ state: 'closed', merged: true }} />);
    expect(screen.getByText(/^merged$/i)).toBeInTheDocument();
  });

  it('shows closed when closed without merge', () => {
    render(<PullRequestStateBadge pullRequest={{ state: 'closed', merged: false }} />);
    expect(screen.getByText(/^closed$/i)).toBeInTheDocument();
  });
});
