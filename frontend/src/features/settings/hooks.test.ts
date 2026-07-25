// frontend/src/features/settings/hooks.test.ts
import { describe, expect, it } from 'vitest';
import { settingsQueryKeys } from '@/features/settings/hooks';

describe('settingsQueryKeys', () => {
  it('builds stable workspace keys', () => {
    expect(settingsQueryKeys.workspace('ws-1')).toEqual(['settings', 'workspace', 'ws-1']);
  });

  it('builds members and invitations keys', () => {
    expect(settingsQueryKeys.members('ws-1')).toEqual(['settings', 'members', 'ws-1']);
    expect(settingsQueryKeys.invitations('ws-1')).toEqual([
      'settings',
      'invitations',
      'ws-1',
      'pending',
    ]);
  });
});
