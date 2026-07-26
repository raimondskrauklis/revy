// frontend/src/features/reviewer/components/JudgeSkippedBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { JudgeSkippedBadge } from '@/features/reviewer/components/JudgeSkippedBadge';

describe('JudgeSkippedBadge', () => {
  it('renders skipped copy when judge disabled', () => {
    render(<JudgeSkippedBadge judgeStatus="skipped_disabled" />);
    expect(screen.getByText('Judge skipped')).toBeInTheDocument();
  });

  it('renders unavailable copy when judge model unavailable', () => {
    render(<JudgeSkippedBadge judgeStatus="skipped_unavailable" />);
    expect(screen.getByText('Judge unavailable')).toBeInTheDocument();
  });

  it('renders nothing when judge completed', () => {
    const { container } = render(<JudgeSkippedBadge judgeStatus="completed" />);
    expect(container).toBeEmptyDOMElement();
  });
});
