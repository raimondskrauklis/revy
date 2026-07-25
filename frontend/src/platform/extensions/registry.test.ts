// frontend/src/platform/extensions/registry.test.ts
import { describe, expect, it, beforeEach } from 'vitest';
import { clearExtensions, getExtensions, registerExtension } from '@/platform/extensions/registry';
import { AppRole, PlatformRole } from '@/shared/types/enums';

function StubCard() {
  return null;
}

describe('extension registry', () => {
  beforeEach(() => {
    clearExtensions();
  });

  it('returns extensions for a slot sorted by order', () => {
    registerExtension({
      id: 'b',
      slot: 'settings_integration',
      component: StubCard,
      order: 20,
    });
    registerExtension({
      id: 'a',
      slot: 'settings_integration',
      component: StubCard,
      order: 10,
    });

    const extensions = getExtensions('settings_integration', AppRole.admin);

    expect(extensions.map((item) => item.id)).toEqual(['a', 'b']);
  });

  it('filters extensions by permission', () => {
    registerExtension({
      id: 'admin-only',
      slot: 'settings_integration',
      component: StubCard,
      permission: 'admin:users',
    });
    registerExtension({
      id: 'viewer',
      slot: 'settings_integration',
      component: StubCard,
      permission: 'items:view',
    });

    const viewerExtensions = getExtensions('settings_integration', AppRole.viewer);
    const adminExtensions = getExtensions('settings_integration', AppRole.admin);

    expect(viewerExtensions.map((item) => item.id)).toEqual(['viewer']);
    expect(adminExtensions.map((item) => item.id)).toEqual(['admin-only', 'viewer']);
  });

  it('grants all extensions to platform super admins', () => {
    registerExtension({
      id: 'admin-only',
      slot: 'settings_integration',
      component: StubCard,
      permission: 'admin:users',
    });

    const extensions = getExtensions('settings_integration', undefined, PlatformRole.super_admin);

    expect(extensions.map((item) => item.id)).toEqual(['admin-only']);
  });
});
