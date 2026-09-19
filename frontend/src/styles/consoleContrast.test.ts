// frontend/src/styles/consoleContrast.test.ts
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const overlayPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), 'tokens.revy.css');

function lin(channel: number): number {
  const c = channel / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string): number {
  const h = hex.replace('#', '');
  const r = Number.parseInt(h.slice(0, 2), 16);
  const g = Number.parseInt(h.slice(2, 4), 16);
  const b = Number.parseInt(h.slice(4, 6), 16);
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrastRatio(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** APCA W3 0.0.98G-4g (absolute Lc). */
function srgbToY(hex: string): number {
  const h = hex.replace('#', '');
  const exp = (channel: number) => (channel / 255) ** 2.4;
  const r = Number.parseInt(h.slice(0, 2), 16);
  const g = Number.parseInt(h.slice(2, 4), 16);
  const b = Number.parseInt(h.slice(4, 6), 16);
  return 0.2126729 * exp(r) + 0.7151522 * exp(g) + 0.072175 * exp(b);
}

function apcaLc(fg: string, bg: string): number {
  const blkThs = 0.022;
  const blkClmp = 1.414;
  const clampY = (y: number) => (y > blkThs ? y : y + (blkThs - y) ** blkClmp);
  const txtY = clampY(srgbToY(fg));
  const bgY = clampY(srgbToY(bg));
  if (Math.abs(bgY - txtY) < 0.0005) {
    return 0;
  }
  let sapc: number;
  let output: number;
  if (bgY > txtY) {
    sapc = (bgY ** 0.56 - txtY ** 0.57) * 1.14;
    output = sapc < 0.1 ? 0 : sapc - 0.027;
  } else {
    sapc = (bgY ** 0.65 - txtY ** 0.62) * 1.14;
    output = sapc > -0.1 ? 0 : sapc + 0.027;
  }
  return Math.abs(output * 100);
}

function parseDarkVars(css: string): Record<string, string> {
  const block = css.match(/html\.dark\s*\{([\s\S]*?)\n\}/);
  if (!block) {
    throw new Error('html.dark block missing');
  }
  const vars: Record<string, string> = {};
  const re = /(--[a-z0-9-]+)\s*:\s*([^;]+);/gi;
  for (const match of block[1].matchAll(re)) {
    vars[match[1]] = match[2].trim();
  }
  return vars;
}

function resolveHex(vars: Record<string, string>, name: string, depth = 0): string {
  const raw = vars[name];
  if (!raw) {
    throw new Error(`missing ${name}`);
  }
  if (raw.startsWith('#')) {
    return raw.toUpperCase();
  }
  const ref = raw.match(/^var\((--[a-z0-9-]+)\)$/i);
  if (ref && depth < 4) {
    return resolveHex(vars, ref[1], depth + 1);
  }
  throw new Error(`unresolved ${name}: ${raw}`);
}

describe('console contrast overlay', () => {
  const css = readFileSync(overlayPath, 'utf8');
  const vars = parseDarkVars(css);

  it('maps surface, text-strong, and chip (not slate leak)', () => {
    expect(resolveHex(vars, '--app-surface')).toBe('#0D1C14');
    expect(resolveHex(vars, '--app-text-strong')).toBe('#D5EAD0');
    expect(resolveHex(vars, '--app-chip')).toBe('#132418');
  });

  it('uncouples info from primary and CTA', () => {
    const info = resolveHex(vars, '--app-info');
    const primary = resolveHex(vars, '--app-primary');
    const cta = resolveHex(vars, '--app-cta-bg');
    expect(info).not.toBe(primary);
    expect(info).not.toBe(cta);
  });

  it('does not use forbidden recipes as body or primary', () => {
    const forbidden = ['#00FF00', '#28E99F', '#39D353'];
    const body = resolveHex(vars, '--app-text');
    const primary = resolveHex(vars, '--app-primary');
    expect(forbidden).not.toContain(body);
    expect(forbidden).not.toContain(primary);
    const assigned = css.replace(/\/\*[\s\S]*?\*\//g, '');
    expect(assigned.toUpperCase()).not.toMatch(/#00FF00|#28E99F|#39D353/);
  });

  it('meets WCAG 2.2 AA and APCA Lc ≥ 75 on named pairs', () => {
    const canvas = resolveHex(vars, '--app-canvas');
    const body = resolveHex(vars, '--app-text');
    const accent = resolveHex(vars, '--app-primary');
    const ctaBg = resolveHex(vars, '--app-cta-bg');
    const ctaFg = resolveHex(vars, '--app-cta-fg');
    const info = resolveHex(vars, '--app-info');
    expect(contrastRatio(body, canvas)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(accent, canvas)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(ctaFg, ctaBg)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(info, canvas)).toBeGreaterThanOrEqual(4.5);
    expect(apcaLc(body, canvas)).toBeGreaterThanOrEqual(75);
    expect(apcaLc(accent, canvas)).toBeGreaterThanOrEqual(75);
    expect(apcaLc(ctaFg, ctaBg)).toBeGreaterThanOrEqual(75);
    expect(apcaLc(info, canvas)).toBeGreaterThanOrEqual(75);
  });
});
