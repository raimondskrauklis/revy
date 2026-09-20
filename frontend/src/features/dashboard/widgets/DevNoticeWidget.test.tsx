// frontend/src/features/dashboard/widgets/DevNoticeWidget.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { DevNoticeWidget } from '@/features/dashboard/widgets/DevNoticeWidget';

describe('DevNoticeWidget', () => {
  it('renders development notice and feedback link', () => {
    render(<DevNoticeWidget />);

    expect(screen.getByRole('heading', { name: /active development/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /feedback/i })).toHaveAttribute(
      'href',
      'https://github.com/raimondskrauklis/revy/issues/new',
    );
  });
});