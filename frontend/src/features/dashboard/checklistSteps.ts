// frontend/src/features/dashboard/checklistSteps.ts
import { hasPermission } from '@/lib/permissions';
import type { MeUser } from '@/lib/me';

export interface ChecklistContext {
  workspaceId: string | null;
  memberCount: number;
  installationCount: number;
}

export interface ChecklistStep {
  id: string;
  labelKey: string;
  href?: string;
  available: boolean | ((me: MeUser) => boolean);
  isComplete: (me: MeUser, ctx: ChecklistContext) => boolean;
}

export interface EvaluatedChecklistStep {
  id: string;
  labelKey: string;
  href?: string;
  isComplete: boolean;
}

export const CHECKLIST_STEPS: ChecklistStep[] = [
  {
    id: 'complete_profile',
    labelKey: 'dashboard.checklist.completeProfile',
    href: '/settings/profile',
    available: true,
    isComplete: (me) => Boolean(me.full_name?.trim()) && me.status === 'active',
  },
  {
    id: 'invite_teammate',
    labelKey: 'dashboard.checklist.inviteTeammate',
    href: '/settings/team',
    available: (me) => hasPermission(me.role ?? undefined, 'admin:users', me.platform_role ?? undefined),
    isComplete: (_me, ctx) => ctx.memberCount > 1,
  },
  {
    id: 'connect_integration',
    labelKey: 'dashboard.checklist.connectIntegration',
    href: '/installations',
    available: true,
    isComplete: (_me, ctx) => ctx.installationCount > 0,
  },
  {
    id: 'setup_billing',
    labelKey: 'dashboard.checklist.setupBilling',
    available: false,
    isComplete: () => false,
  },
];

function isStepAvailable(step: ChecklistStep, me: MeUser): boolean {
  return typeof step.available === 'function' ? step.available(me) : step.available;
}

export function evaluateChecklist(
  me: MeUser,
  ctx: ChecklistContext,
): EvaluatedChecklistStep[] {
  return CHECKLIST_STEPS.filter((step) => isStepAvailable(step, me)).map((step) => ({
    id: step.id,
    labelKey: step.labelKey,
    href: step.href,
    isComplete: step.isComplete(me, ctx),
  }));
}

export function hasIncompleteChecklistSteps(
  me: MeUser,
  ctx: ChecklistContext,
): boolean {
  return evaluateChecklist(me, ctx).some((step) => !step.isComplete);
}
