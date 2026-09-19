// frontend/src/features/reviewer/ReviewerNavItem.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ReviewerNavItem } from '@/features/reviewer/ReviewerNavItem';

vi.mock('@/features/reviewer/hooks', () => ({
  useReviewerAvailability: vi.fn(() => ({ data: false, isLoading: false })),
}));

describe('ReviewerNavItem', () => {
  it('renders the reviewer link when availability is false', () => {
    render(
      <MemoryRouter>
        <ul>
          <ReviewerNavItem />
        </ul>
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: /reviewer/i })).toHaveAttribute('href', '/reviewer');
  });
});
