// frontend/src/components/ui/TableSkeleton.test.tsx
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TableSkeleton } from '@/components/ui/TableSkeleton';

describe('TableSkeleton', () => {
  it('renders default 4 rows', () => {
    const { container } = render(<TableSkeleton />);
    const rows = container.querySelectorAll('tbody tr');
    expect(rows.length).toBe(4);
  });

  it('renders custom row count', () => {
    const { container } = render(<TableSkeleton rows={3} />);
    const rows = container.querySelectorAll('tbody tr');
    expect(rows.length).toBe(3);
  });

  it('renders skeleton bars with animate-pulse', () => {
    const { container } = render(<TableSkeleton />);
    const bars = container.querySelectorAll('.animate-pulse');
    expect(bars.length).toBeGreaterThan(0);
  });
});