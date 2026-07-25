// frontend/src/features/settings/components/PermissionsMatrix.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PermissionsMatrix } from '@/features/settings/components/PermissionsMatrix';

describe('PermissionsMatrix', () => {
  it('renders role permission rows', () => {
    render(<PermissionsMatrix />);

    expect(screen.getByText(/role permissions/i)).toBeInTheDocument();
    expect(screen.getByText(/^admin$/i)).toBeInTheDocument();
    expect(screen.getByText(/^operator$/i)).toBeInTheDocument();
    expect(screen.getByText(/^viewer$/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^yes$/i).length).toBeGreaterThan(0);
  });
});
