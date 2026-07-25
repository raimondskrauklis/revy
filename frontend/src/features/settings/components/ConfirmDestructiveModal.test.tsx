// frontend/src/features/settings/components/ConfirmDestructiveModal.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ConfirmDestructiveModal } from '@/features/settings/components/ConfirmDestructiveModal';

describe('ConfirmDestructiveModal', () => {
  it('calls onConfirm without typed match when confirmMatch is omitted', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    render(
      <ConfirmDestructiveModal
        open
        title="Delete item"
        description="This cannot be undone."
        confirmLabel="Delete"
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />,
    );

    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('requires typed confirmation before enabling confirm', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    render(
      <ConfirmDestructiveModal
        open
        title="Delete workspace"
        description="Permanent action."
        confirmLabel="Delete workspace"
        confirmMatch="acme"
        confirmMatchLabel="Type acme to confirm"
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />,
    );

    const confirmButton = screen.getByRole('button', { name: /delete workspace/i });
    expect(confirmButton).toBeDisabled();

    await user.type(screen.getByLabelText(/type acme/i), 'acme');
    await user.click(confirmButton);

    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('does not render when closed', () => {
    render(
      <ConfirmDestructiveModal
        open={false}
        title="Hidden"
        description="Hidden"
        confirmLabel="Confirm"
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
