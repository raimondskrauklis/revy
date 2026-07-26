// frontend/src/features/settings/pages/ReviewSettingsPage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ReviewSettingsPage } from '@/features/settings/pages/ReviewSettingsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/settings/api', () => ({
  fetchWorkspace: vi.fn(),
  fetchModelPolicy: vi.fn(),
  fetchModelCatalog: vi.fn(),
  patchWorkspace: vi.fn(),
  patchModelPolicy: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { fetchModelCatalog, fetchModelPolicy, fetchWorkspace } from '@/features/settings/api';

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ReviewSettingsPage />
    </QueryClientProvider>,
  );
}

describe('ReviewSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchWorkspace).mockResolvedValue({
      id: 'ws-1',
      name: 'Acme',
      slug: 'acme',
      status: 'active',
      review_autostart_enabled: true,
    });
    vi.mocked(fetchModelPolicy).mockResolvedValue({
      overrides: {},
      effective: {
        reviewer_standard: { provider: 'moonshot', model_id: 'kimi-k2.7-code' },
        reviewer_deep: { provider: 'moonshot', model_id: 'kimi-k3' },
        reviewer_critical: { provider: 'moonshot', model_id: 'kimi-k3' },
        judge: { provider: 'anthropic', model_id: 'claude-sonnet-4-20250514' },
      },
    });
    vi.mocked(fetchModelCatalog).mockResolvedValue({
      roles: {
        reviewer_standard: [
          { provider: 'moonshot', model_id: 'kimi-k2.7-code', display_name: 'Kimi K2.7 Code' },
        ],
        judge: [
          {
            provider: 'anthropic',
            model_id: 'claude-sonnet-4-20250514',
            display_name: 'Claude Sonnet',
          },
        ],
      },
    });
  });

  it('renders automation and model sections', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [],
      },
    } as unknown as ReturnType<typeof useAuth>);

    renderPage();

    expect(await screen.findByRole('heading', { name: /^review$/i })).toBeInTheDocument();
    expect(screen.getByText(/automated reviews/i)).toBeInTheDocument();
    expect(screen.getByText(/models/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });
});
