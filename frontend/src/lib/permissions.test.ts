// frontend/src/lib/permissions.test.ts
import { describe, expect, it } from 'vitest';
import { AppRole, PlatformRole } from '@/shared/types/enums';
import { canManageWorkspaces, hasPermission } from '@/lib/permissions';

describe('hasPermission', () => {
  it('grants platform super_admin all permissions', () => {
    expect(hasPermission(undefined, 'admin:system', PlatformRole.super_admin)).toBe(true);
  });

  it('denies viewer items:manage', () => {
    expect(hasPermission(AppRole.viewer, 'items:manage')).toBe(false);
  });

  it('canManageWorkspaces is platform only', () => {
    expect(canManageWorkspaces(PlatformRole.super_admin)).toBe(true);
    expect(canManageWorkspaces(undefined)).toBe(false);
  });
});
