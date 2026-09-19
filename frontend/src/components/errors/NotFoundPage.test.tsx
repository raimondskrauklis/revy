// frontend/src/components/errors/NotFoundPage.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { NotFoundPage } from '@/components/errors/NotFoundPage';

describe('NotFoundPage', () => {
  it('links home to dashboard', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: /go home/i })).toHaveAttribute('href', '/dashboard');
  });
});
