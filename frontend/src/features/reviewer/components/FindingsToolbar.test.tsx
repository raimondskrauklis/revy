// frontend/src/features/reviewer/components/FindingsToolbar.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { act } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FindingsToolbar } from '@/features/reviewer/components/FindingsToolbar';
import type { ReconciledFinding } from '@/features/reviewer/types';

function f(overrides: Partial<ReconciledFinding>): ReconciledFinding {
  return {
    id: '1',
    pull_request_id: 'pr',
    category: 'bug',
    title: 'Test finding',
    message: 'Something wrong',
    file_path: 'src/app.ts',
    last_seen_revision_id: 'rev',
    severity: 'warning',
    state: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function renderToolbar(findings: ReconciledFinding[] = [f({})]) {
  let captured: ReconciledFinding[] = [];
  const children = (filtered: ReconciledFinding[]) => {
    captured = filtered;
    return <div data-testid="child">{filtered.length} items</div>;
  };
  const result = render(
    <FindingsToolbar findings={findings}>
      {children}
    </FindingsToolbar>,
  );
  return { ...result, getCaptured: () => captured };
}

describe('FindingsToolbar', () => {
  it('renders search input', () => {
    renderToolbar();
    expect(screen.getByPlaceholderText(/Search findings/i)).toBeInTheDocument();
  });

  it('shows result count', () => {
    renderToolbar();
    expect(screen.getByText(/1 finding/i)).toBeInTheDocument();
  });

  it('passes filtered findings to children', () => {
    const findings = [
      f({ id: '1', title: 'Cross-site scripting' }),
      f({ id: '2', title: 'Memory leak' }),
    ];
    const { getCaptured } = renderToolbar(findings);
    expect(getCaptured()).toHaveLength(2);
  });

  it('renders child content', () => {
    renderToolbar();
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('renders severity filter chips', () => {
    renderToolbar();
    expect(screen.getByText(/critical/i)).toBeInTheDocument();
    expect(screen.getByText(/error/i)).toBeInTheDocument();
    expect(screen.getByText(/warning/i)).toBeInTheDocument();
    expect(screen.getByText(/info/i)).toBeInTheDocument();
  });

  it('renders sort headers', () => {
    renderToolbar();
    const sortHeaders = screen.getAllByText(/Severity/);
    expect(sortHeaders.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/File/)).toBeInTheDocument();
    expect(screen.getByText(/Date/)).toBeInTheDocument();
  });

  it('shows clear filters button when search is entered', () => {
    renderToolbar();
    const input = screen.getByPlaceholderText(/Search findings/i);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    expect(screen.getByText(/Clear filters/i)).toBeInTheDocument();
  });
});