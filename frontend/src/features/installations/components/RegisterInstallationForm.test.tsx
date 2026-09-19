// frontend/src/features/installations/components/RegisterInstallationForm.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { RegisterInstallationForm } from '@/features/installations/components/RegisterInstallationForm';
import { GitHubAccountType } from '@/shared/types/enums';

describe('RegisterInstallationForm', () => {
  it('submits typed installation payload', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(<RegisterInstallationForm onSubmit={onSubmit} submitting={false} />);

    await user.type(screen.getByLabelText(/github installation id/i), '12345');
    await user.type(screen.getByLabelText(/account login/i), 'acme');
    await user.type(screen.getByLabelText(/github account id/i), '99');
    await user.click(screen.getByRole('button', { name: /register installation/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      github_installation_id: 12345,
      account_login: 'acme',
      account_type: GitHubAccountType.organization,
      account_id: 99,
    });
  });
});
