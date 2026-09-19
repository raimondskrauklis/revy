// frontend/src/features/installations/components/ConnectGitHubPanel.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ConnectGitHubPanel } from '@/features/installations/components/ConnectGitHubPanel';
import { GitHubAccountType } from '@/shared/types/enums';

describe('ConnectGitHubPanel', () => {
  it('calls onConnect from Install Revy and does not submit the fallback form', async () => {
    const user = userEvent.setup();
    const onConnect = vi.fn().mockResolvedValue(undefined);
    const onFallbackSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <ConnectGitHubPanel
        connecting={false}
        submittingFallback={false}
        onConnect={onConnect}
        onFallbackSubmit={onFallbackSubmit}
      />,
    );

    await user.click(screen.getByRole('button', { name: /install revy/i }));

    expect(onConnect).toHaveBeenCalledTimes(1);
    expect(onFallbackSubmit).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: /register installation/i })).not.toBeInTheDocument();
  });

  it('submits fallback payload only after opening the details', async () => {
    const user = userEvent.setup();
    const onConnect = vi.fn().mockResolvedValue(undefined);
    const onFallbackSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <ConnectGitHubPanel
        connecting={false}
        submittingFallback={false}
        onConnect={onConnect}
        onFallbackSubmit={onFallbackSubmit}
      />,
    );

    await user.click(screen.getByText(/manual installation id/i));
    await user.type(screen.getByLabelText(/github installation id/i), '12345');
    await user.type(screen.getByLabelText(/account login/i), 'acme');
    await user.type(screen.getByLabelText(/github account id/i), '99');
    await user.click(screen.getByRole('button', { name: /register installation/i }));

    expect(onFallbackSubmit).toHaveBeenCalledWith({
      github_installation_id: 12345,
      account_login: 'acme',
      account_type: GitHubAccountType.organization,
      account_id: 99,
    });
    expect(onConnect).not.toHaveBeenCalled();
  });
});
