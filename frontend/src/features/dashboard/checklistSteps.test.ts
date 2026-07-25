// frontend/src/features/dashboard/checklistSteps.test.ts
import { describe, expect, it } from 'vitest';
import { evaluateChecklist, hasIncompleteChecklistSteps } from '@/features/dashboard/checklistSteps';
import type { MeUser } from '@/lib/me';
import { AppRole } from '@/shared/types/enums';

function baseUser(overrides: Partial<MeUser> = {}): MeUser {
  return {
    id: '1',
    email: 'admin@example.com',
    full_name: 'Admin User',
    status: 'active',
    platform_role: null,
    workspace_id: 'ws-1',
    workspace_plan: null,
    role: AppRole.admin,
    memberships: [],
    locale: 'en',
    timezone: 'UTC',
    ...overrides,
  };
}

const baseContext = {
  workspaceId: 'ws-1',
  memberCount: 1,
  installationCount: 0,
  plan: 'free',
};

describe('checklistSteps', () => {
  it('shows billing step for admins when not on pro', () => {
    const steps = evaluateChecklist(baseUser(), baseContext);
    const billing = steps.find((step) => step.id === 'setup_billing');

    expect(billing).toBeDefined();
    expect(billing?.isComplete).toBe(false);
    expect(billing?.href).toBe('/settings/billing');
  });

  it('marks billing complete on pro plan', () => {
    const steps = evaluateChecklist(baseUser(), { ...baseContext, plan: 'pro' });
    const billing = steps.find((step) => step.id === 'setup_billing');

    expect(billing?.isComplete).toBe(true);
  });

  it('hides billing step for viewers', () => {
    const steps = evaluateChecklist(baseUser({ role: AppRole.viewer }), baseContext);

    expect(steps.map((step) => step.id)).not.toContain('setup_billing');
  });

  it('marks profile complete when name and status are valid', () => {
    const steps = evaluateChecklist(baseUser(), baseContext);
    const profile = steps.find((step) => step.id === 'complete_profile');

    expect(profile?.isComplete).toBe(true);
  });

  it('shows invite step incomplete for single-member workspace', () => {
    const steps = evaluateChecklist(baseUser(), baseContext);
    const invite = steps.find((step) => step.id === 'invite_teammate');

    expect(invite?.isComplete).toBe(false);
  });

  it('hides invite step for viewers', () => {
    const steps = evaluateChecklist(
      baseUser({ role: AppRole.viewer }),
      { ...baseContext, memberCount: 2 },
    );

    expect(steps.map((step) => step.id)).not.toContain('invite_teammate');
  });

  it('detects incomplete steps', () => {
    expect(hasIncompleteChecklistSteps(baseUser(), baseContext)).toBe(true);
    expect(
      hasIncompleteChecklistSteps(baseUser(), {
        ...baseContext,
        memberCount: 2,
        installationCount: 1,
        plan: 'pro',
      }),
    ).toBe(false);
  });
});
