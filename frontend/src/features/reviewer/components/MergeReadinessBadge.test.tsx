// frontend/src/features/reviewer/components/MergeReadinessBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MergeReadinessBadge } from '@/features/reviewer/components/MergeReadinessBadge';

describe('MergeReadinessBadge', () => {
  it('shows not published when publish job absent', () => {
    render(<MergeReadinessBadge conclusion="success" published={false} />);
    expect(screen.getByText(/not published/i)).toBeInTheDocument();
  });

  it('shows failure label when published with failure conclusion', () => {
    render(<MergeReadinessBadge conclusion="failure" published />);
    expect(screen.getByText(/blocking findings/i)).toBeInTheDocument();
  });
});
