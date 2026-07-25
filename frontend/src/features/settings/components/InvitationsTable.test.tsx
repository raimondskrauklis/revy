// frontend/src/features/settings/components/InvitationsTable.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { InvitationsTable } from '@/features/settings/components/InvitationsTable';
import { AppRole } from '@/shared/types/enums';

describe('InvitationsTable', () => {
  const invitation = {
    id: 'inv-1',
    email: 'new@example.com',
    role: AppRole.viewer,
    status: 'pending' as const,
    expires_at: '2026-12-31T00:00:00Z',
    created_at: '2026-01-01T00:00:00Z',
  };

  it('renders invitation rows', () => {
    render(
      <InvitationsTable invitations={[invitation]} busyInvitationId={null} onRevoke={vi.fn()} />,
    );

    expect(screen.getByText('new@example.com')).toBeInTheDocument();
  });

  it('confirms before revoking an invitation', async () => {
    const onRevoke = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(
      <InvitationsTable invitations={[invitation]} busyInvitationId={null} onRevoke={onRevoke} />,
    );

    await user.click(screen.getByRole('button', { name: /revoke/i }));
    await user.click(screen.getByRole('button', { name: /confirm/i }));

    expect(onRevoke).toHaveBeenCalledWith('inv-1');
  });
});
