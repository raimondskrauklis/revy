// frontend/src/features/admin/components/ImpersonationStartModal.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ImpersonationStartModal } from '@/features/admin/components/ImpersonationStartModal';

describe('ImpersonationStartModal', () => {
  it('requires a reason of at least 10 characters', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    render(
      <ImpersonationStartModal
        targetEmail="member@example.com"
        busy={false}
        onCancel={() => undefined}
        onConfirm={onConfirm}
      />,
    );

    const startButton = screen.getByRole('button', { name: /start impersonation/i });
    expect(startButton).toBeDisabled();

    await user.type(screen.getByLabelText(/reason/i), 'short');
    expect(startButton).toBeDisabled();

    await user.clear(screen.getByLabelText(/reason/i));
    await user.type(screen.getByLabelText(/reason/i), 'Support ticket #42 — billing issue');
    expect(startButton).not.toBeDisabled();

    await user.click(startButton);
    expect(onConfirm).toHaveBeenCalledWith('Support ticket #42 — billing issue');
  });
});
