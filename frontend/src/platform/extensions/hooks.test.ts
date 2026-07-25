// frontend/src/platform/extensions/hooks.test.ts
import { describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useExtensions } from '@/platform/extensions/hooks';
import { registerExtension, clearExtensions } from '@/platform/extensions/registry';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

function TestWidget() {
  return null;
}

describe('useExtensions', () => {
  it('filters pro extensions using workspace_plan from me without billing API', () => {
    clearExtensions();
    registerExtension({
      id: 'free-widget',
      slot: 'dashboard_widget',
      component: TestWidget,
      order: 1,
    });
    registerExtension({
      id: 'pro-widget',
      slot: 'dashboard_widget',
      component: TestWidget,
      minPlan: 'pro',
      order: 2,
    });

    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'viewer@example.com',
        full_name: 'Viewer',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: 'free',
        role: AppRole.viewer,
        memberships: [],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    const { result } = renderHook(() => useExtensions('dashboard_widget'));

    expect(result.current.map((item) => item.id)).toEqual(['free-widget']);
  });
});
