// frontend/src/lib/api.ts
import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import i18n from '@/i18n/config';
import { requireViteEnv } from '@/lib/env';
import { getKeycloakInstance, getPostLogoutRedirectUri } from '@/lib/keycloak';
import { log } from '@/lib/log';
import { toast } from '@/lib/toast';

const ACTIVE_WORKSPACE_STORAGE_KEY = 'active_workspace_id';

export const apiClient = axios.create({
  baseURL: requireViteEnv('VITE_API_BASE_URL'),
  headers: { 'Content-Type': 'application/json' },
});

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

export function getStoredWorkspaceId(): string | null {
  return localStorage.getItem(ACTIVE_WORKSPACE_STORAGE_KEY);
}

export function setStoredWorkspaceId(workspaceId: string | null): void {
  if (workspaceId) {
    localStorage.setItem(ACTIVE_WORKSPACE_STORAGE_KEY, workspaceId);
  } else {
    localStorage.removeItem(ACTIVE_WORKSPACE_STORAGE_KEY);
  }
}

export async function logoutKeycloakSession(): Promise<void> {
  setStoredWorkspaceId(null);
  const keycloak = getKeycloakInstance();
  await keycloak?.logout({ redirectUri: getPostLogoutRedirectUri() });
}

async function refreshKeycloakToken(): Promise<string | null> {
  const keycloak = getKeycloakInstance();
  if (!keycloak?.authenticated) return null;

  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      await keycloak.updateToken(30);
      return keycloak.token ?? null;
    } catch (error) {
      log.warn('token_refresh_failed', { reason: String(error) });
      toast.error(
        i18n.t('auth.sessionExpired.title'),
        i18n.t('auth.sessionExpired.body'),
      );
      await logoutKeycloakSession();
      return null;
    } finally {
      setTimeout(() => {
        isRefreshing = false;
        refreshPromise = null;
      }, 100);
    }
  })();

  return refreshPromise;
}

apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const keycloak = getKeycloakInstance();
    if (keycloak?.authenticated) {
      if (keycloak.isTokenExpired(10)) {
        const token = await refreshKeycloakToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } else if (keycloak.token && config.headers) {
        config.headers.Authorization = `Bearer ${keycloak.token}`;
      }
    }

    const workspaceId = getStoredWorkspaceId();
    if (workspaceId && config.headers) {
      config.headers['X-Workspace-Id'] = workspaceId;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const body = error.response?.data as { error?: string } | undefined;
    if (error.response?.status === 403 && body?.error === 'workspace_suspended') {
      if (!window.location.pathname.startsWith('/workspace-suspended')) {
        window.location.assign('/workspace-suspended');
      }
      return Promise.reject(error);
    }

    const keycloak = getKeycloakInstance();
    if (error.response?.status === 401 && keycloak) {
      const isMe = error.config?.url?.includes('/me');
      if (!isMe) {
        toast.error(
          i18n.t('auth.sessionExpired.title'),
          i18n.t('auth.sessionExpired.body'),
        );
        await logoutKeycloakSession();
      }
    }
    return Promise.reject(error);
  },
);

export async function parseSuccess<T>(response: { data: unknown }): Promise<T> {
  const body = response.data;
  if (body && typeof body === 'object' && 'success' in body && (body as { success: boolean }).success) {
    return (body as unknown as { data: T }).data;
  }
  return body as T;
}

export default apiClient;
