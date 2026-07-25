// frontend/src/features/settings/pages/DangerZonePage.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DangerZonePage } from '@/features/settings/pages/DangerZonePage';
import { AppRole } from '@/shared/types/enums';

const mockNavigate = vi.fn();
const mockLogout = vi.fn();
const mockRefetchUser = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/settings/hooks', () => ({
  useCreateExportJob: vi.fn(),
  useExportJobStatus: vi.fn(),
  useLeaveWorkspace: vi.fn(),
  useDeleteWorkspace: vi.fn(),
  useDeleteAccount: vi.fn(),
  downloadUserExport: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import {
  downloadUserExport,
  useCreateExportJob,
  useDeleteAccount,
  useDeleteWorkspace,
  useExportJobStatus,
  useLeaveWorkspace,
} from '@/features/settings/hooks';

function renderPage() {
  return render(
    <MemoryRouter>
      <DangerZonePage />
    </MemoryRouter>,
  );
}

describe('DangerZonePage', () => {
  it('requests export and shows completed download action', async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({ job_id: 'job-1' });

    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.viewer,
        memberships: [
          {
            workspace_id: 'ws-1',
            workspace_name: 'Acme',
            workspace_slug: 'acme',
            role: AppRole.viewer,
          },
        ],
        locale: 'en',
        timezone: 'UTC',
      },
      logout: mockLogout,
      refetchUser: mockRefetchUser,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useCreateExportJob).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateExportJob>);
    vi.mocked(useExportJobStatus).mockReturnValue({
      data: { status: 'completed', created_at: '', completed_at: '', expires_at: '' },
      isLoading: false,
    } as unknown as ReturnType<typeof useExportJobStatus>);
    vi.mocked(useLeaveWorkspace).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useLeaveWorkspace>);
    vi.mocked(useDeleteWorkspace).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteWorkspace>);
    vi.mocked(useDeleteAccount).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteAccount>);
    vi.mocked(downloadUserExport).mockResolvedValue(new Blob(['zip']));

    renderPage();

    await user.click(screen.getByRole('button', { name: /request export/i }));
    expect(mutateAsync).toHaveBeenCalledOnce();

    await user.click(screen.getByRole('button', { name: /download export/i }));
    expect(downloadUserExport).toHaveBeenCalledWith('job-1');
  });

  it('shows delete workspace section for admins only', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [
          {
            workspace_id: 'ws-1',
            workspace_name: 'Acme',
            workspace_slug: 'acme',
            role: AppRole.admin,
          },
        ],
        locale: 'en',
        timezone: 'UTC',
      },
      logout: mockLogout,
      refetchUser: mockRefetchUser,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useCreateExportJob).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateExportJob>);
    vi.mocked(useExportJobStatus).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useExportJobStatus>);
    vi.mocked(useLeaveWorkspace).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useLeaveWorkspace>);
    vi.mocked(useDeleteWorkspace).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteWorkspace>);
    vi.mocked(useDeleteAccount).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteAccount>);

    renderPage();

    expect(screen.getByRole('button', { name: /delete workspace/i })).toBeInTheDocument();
  });

  it('logs out after account deletion', async () => {
    const user = userEvent.setup();
    const deleteAccount = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.viewer,
        memberships: [
          {
            workspace_id: 'ws-1',
            workspace_name: 'Acme',
            workspace_slug: 'acme',
            role: AppRole.viewer,
          },
        ],
        locale: 'en',
        timezone: 'UTC',
      },
      logout: mockLogout,
      refetchUser: mockRefetchUser,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useCreateExportJob).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateExportJob>);
    vi.mocked(useExportJobStatus).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useExportJobStatus>);
    vi.mocked(useLeaveWorkspace).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useLeaveWorkspace>);
    vi.mocked(useDeleteWorkspace).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteWorkspace>);
    vi.mocked(useDeleteAccount).mockReturnValue({
      mutateAsync: deleteAccount,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteAccount>);

    renderPage();

    await user.click(screen.getByRole('button', { name: /^delete account$/i }));
    await user.type(screen.getByLabelText(/type user@example.com/i), 'user@example.com');
    await user.click(screen.getAllByRole('button', { name: /^delete account$/i })[1]);

    expect(deleteAccount).toHaveBeenCalledWith({ confirm_email: 'user@example.com' });
    expect(mockLogout).toHaveBeenCalledOnce();
  });
});
