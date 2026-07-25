// frontend/src/features/admin/pages/AuditSearchPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { AuditSearchPage } from '@/features/admin/pages/AuditSearchPage';

vi.mock('@/features/admin/api', () => ({
  fetchPlatformAudit: vi.fn(),
}));

import { fetchPlatformAudit } from '@/features/admin/api';

describe('AuditSearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state', async () => {
    vi.mocked(fetchPlatformAudit).mockResolvedValue({
      items: [],
      cursor: { next_cursor: null, has_next: false },
    });

    render(<AuditSearchPage />);

    await waitFor(() => {
      expect(screen.getByText(/no audit events found/i)).toBeInTheDocument();
    });
  });

  it('lists audit events with impersonator column', async () => {
    vi.mocked(fetchPlatformAudit).mockResolvedValue({
      items: [
        {
          id: 'a1',
          created_at: '2026-01-01T12:00:00Z',
          action: 'platform.workspace.viewed',
          resource_type: 'workspace',
          resource_id: 'ws-1',
          actor_user_id: 'u1',
          actor_email: 'member@example.com',
          impersonator_user_id: 'admin-1',
          impersonator_email: 'admin@example.com',
          metadata: {},
          workspace_id: 'ws-1',
        },
      ],
      cursor: { next_cursor: null, has_next: false },
    });

    render(<AuditSearchPage />);

    await waitFor(() => {
      expect(screen.getByText(/workspace viewed/i)).toBeInTheDocument();
      expect(screen.getByText('member@example.com')).toBeInTheDocument();
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });
  });
});
