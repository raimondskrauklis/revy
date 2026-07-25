// frontend/src/features/settings/components/InviteMemberForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { InviteMemberForm } from '@/features/settings/components/InviteMemberForm';
import { AppRole } from '@/shared/types/enums';

describe('InviteMemberForm', () => {
  it('submits invite payload', async () => {
    const onInvite = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<InviteMemberForm onInvite={onInvite} />);

    await user.type(screen.getByLabelText(/email/i), 'new@example.com');
    await user.click(screen.getByRole('button', { name: /send invitation/i }));

    await waitFor(() => {
      expect(onInvite).toHaveBeenCalledWith({
        email: 'new@example.com',
        role: AppRole.viewer,
      });
    });
  });
});
