// frontend/src/features/installations/components/InstallationsTable.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { InstallationsTable } from '@/features/installations/components/InstallationsTable';
import { GitHubAccountType, GitHubInstallationStatus } from '@/shared/types/enums';
import type { GitHubInstallation } from '@/features/installations/api';

function installation(overrides: Partial<GitHubInstallation> = {}): GitHubInstallation {
  return {
    id: 'inst-1',
    workspace_id: 'ws-1',
    github_installation_id: 12345,
    account_login: 'acme',
    account_type: GitHubAccountType.organization,
    account_id: 7,
    status: GitHubInstallationStatus.active,
    permissions_snapshot: null,
    verified_at: null,
    created_at: '2026-09-19T10:00:00.000Z',
    updated_at: '2026-09-19T10:00:00.000Z',
    ...overrides,
  };
}

describe('InstallationsTable', () => {
  it('links unverified rows to GitHub Configure', () => {
    render(<InstallationsTable installations={[installation()]} />);

    const link = screen.getByRole('link', { name: /configure on github/i });
    expect(link).toHaveAttribute('href', 'https://github.com/settings/installations/12345');
  });

  it('does not show Configure when verified_at is set', () => {
    render(
      <InstallationsTable
        installations={[installation({ verified_at: '2026-09-19T11:00:00.000Z' })]}
      />,
    );

    expect(screen.queryByRole('link', { name: /configure on github/i })).not.toBeInTheDocument();
  });
});
