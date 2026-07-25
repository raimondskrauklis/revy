// frontend/src/lib/keycloak.ts
import Keycloak from 'keycloak-js';
import { optionalViteEnv, requireViteEnv } from '@/lib/env';

let keycloakInstance: Keycloak | null = null;
let isInitialized = false;

export interface KeycloakConfig {
  url: string;
  realm: string;
  clientId: string;
}

export function initKeycloak(): Keycloak {
  if (keycloakInstance) {
    return keycloakInstance;
  }

  const config: KeycloakConfig = {
    url: requireViteEnv('VITE_KEYCLOAK_URL'),
    realm: requireViteEnv('VITE_KEYCLOAK_REALM'),
    clientId: requireViteEnv('VITE_KEYCLOAK_CLIENT_ID'),
  };

  keycloakInstance = new Keycloak(config);
  isInitialized = false;
  return keycloakInstance;
}

export function getKeycloakInstance(): Keycloak | null {
  return keycloakInstance;
}

export function setKeycloakInitialized(): void {
  isInitialized = true;
}

export function isKeycloakInitialized(): boolean {
  return isInitialized || keycloakInstance?.token !== undefined;
}

export function resetKeycloak(): void {
  keycloakInstance = null;
  isInitialized = false;
}

export function getKeycloakAccountUrl(): string {
  const override = optionalViteEnv('VITE_KEYCLOAK_ACCOUNT_URL');
  if (override) {
    return override;
  }
  const baseUrl = requireViteEnv('VITE_KEYCLOAK_URL').replace(/\/$/, '');
  const realm = requireViteEnv('VITE_KEYCLOAK_REALM');
  return `${baseUrl}/realms/${realm}/account`;
}

export function getKeycloakAdminConsoleUrl(): string {
  const override = optionalViteEnv('VITE_KEYCLOAK_ADMIN_URL');
  if (override) {
    return override;
  }
  const baseUrl = requireViteEnv('VITE_KEYCLOAK_URL').replace(/\/$/, '');
  const realm = requireViteEnv('VITE_KEYCLOAK_REALM');
  return `${baseUrl}/admin/${realm}/console/`;
}
