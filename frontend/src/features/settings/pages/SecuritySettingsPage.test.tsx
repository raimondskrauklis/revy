// frontend/src/features/settings/pages/SecuritySettingsPage.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SecuritySettingsPage } from '@/features/settings/pages/SecuritySettingsPage';

describe('SecuritySettingsPage', () => {
  it('explains that sign-in security is not managed here yet', () => {
    render(<SecuritySettingsPage />);

    expect(screen.getByRole('heading', { name: /^security$/i })).toBeInTheDocument();
    expect(screen.getByText(/not available yet/i)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    expect(screen.queryByText(/keycloak/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/account console/i)).not.toBeInTheDocument();
  });
});
