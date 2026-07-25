// frontend/src/features/settings/components/MembersTable.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { MembersTable } from '@/features/settings/components/MembersTable';
import { AppRole } from '@/shared/types/enums';

describe('MembersTable', () => {
  const member = {
    user_id: 'u-1',
    email: 'member@example.com',
    full_name: 'Member',
    role: AppRole.operator,
    created_at: '2026-01-01T00:00:00Z',
  };

  it('renders member rows read-only for non-admins', () => {
    render(
      <MembersTable
        members={[member]}
        canManage={false}
        busyUserId={null}
        onRoleChange={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByText('member@example.com')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /remove/i })).not.toBeInTheDocument();
  });

  it('confirms before removing a member', async () => {
    const onRemove = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(
      <MembersTable
        members={[member]}
        canManage
        busyUserId={null}
        onRoleChange={vi.fn()}
        onRemove={onRemove}
      />,
    );

    await user.click(screen.getByRole('button', { name: /remove/i }));
    await user.click(screen.getByRole('button', { name: /confirm/i }));

    expect(onRemove).toHaveBeenCalledWith('u-1');
  });
});
