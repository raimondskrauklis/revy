// frontend/src/features/reviewer/ReviewerNavItem.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { ReviewerNavItem } from '@/features/reviewer/ReviewerNavItem';

describe('ReviewerNavItem', () => {
  it('renders the reviewer link', () => {
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
