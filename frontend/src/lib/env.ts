// frontend/src/lib/env.ts
/** Vite env validation — docs/backend/CONFIG.md */

export function requireViteEnv(name: string): string {
  const value = import.meta.env[name];
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value.trim();
}

export function optionalViteEnv(name: string): string | undefined {
  const value = import.meta.env[name];
  if (typeof value !== 'string' || value.trim() === '') {
    return undefined;
  }
  return value.trim();
}
