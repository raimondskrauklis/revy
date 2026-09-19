// frontend/src/lib/toast.richColors.test.ts
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const srcDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

describe('toast tokens', () => {
  it('does not enable Sonner richColors', () => {
    const main = readFileSync(path.join(srcDir, 'main.tsx'), 'utf8');
    const toast = readFileSync(path.join(srcDir, 'lib/toast.ts'), 'utf8');
    expect(main).not.toMatch(/richColors/);
    expect(toast).not.toMatch(/richColors/);
    expect(main).toMatch(/theme=["']dark["']/);
  });
});
