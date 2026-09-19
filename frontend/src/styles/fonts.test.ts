// frontend/src/styles/fonts.test.ts
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const srcDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

describe('Plex @theme map', () => {
  it('maps sans and mono to IBM Plex in index.css', () => {
    const css = readFileSync(path.join(srcDir, 'index.css'), 'utf8');
    expect(css).toMatch(/@theme/);
    expect(css).toMatch(/--font-sans:[^;]*IBM Plex Sans/);
    expect(css).toMatch(/--font-mono:[^;]*IBM Plex Mono/);
    expect(css).toMatch(/@fontsource\/ibm-plex-sans/);
    expect(css).toMatch(/@fontsource\/ibm-plex-mono/);
  });

  it('does not load fonts from Google or Typekit', () => {
    const html = readFileSync(path.resolve(srcDir, '../index.html'), 'utf8');
    expect(html).not.toMatch(/fonts\.googleapis|typekit/i);
  });
});
