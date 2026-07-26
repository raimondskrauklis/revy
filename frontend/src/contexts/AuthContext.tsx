// frontend/src/contexts/AuthContext.tsx
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import type Keycloak from 'keycloak-js';
import { fetchMe, syncStoredWorkspace, type MeUser } from '@/lib/me';
import { normalizeLanguage } from '@/lib/locale';
import i18n from '@/i18n/config';
import {
  getKeycloakInstance,
  initKeycloak,
  setKeycloakInitialized,
} from '@/lib/keycloak';
import { log } from '@/lib/log';
import { Sentry } from '@/lib/sentry';
import { mapApiError, showDomainErrorToast } from '@/shared/errors';
import { logoutKeycloakSession } from '@/lib/api';

const PROVISION_ERROR_CODES = new Set(['provision_email_required', 'identity_email_conflict']);

interface AuthContextValue {
  keycloak: Keycloak | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isUserLoading: boolean;
  user: MeUser | null;
  login: (redirectPath?: string) => void;
  logout: () => void;
  refetchUser: () => Promise<MeUser | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [keycloak, setKeycloak] = useState<Keycloak | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<MeUser | null>(null);
  const [isUserLoading, setIsUserLoading] = useState(false);
  const initialized = useRef(false);
  const postLoginRedirect = useRef<string | undefined>(undefined);

  const refetchUser = useCallback(async (): Promise<MeUser | null> => {
    const keycloak = getKeycloakInstance();
    if (!keycloak?.authenticated) {
      setUser(null);
      return null;
    }
    setIsUserLoading(true);
    try {
      const me = syncStoredWorkspace(await fetchMe());
      await i18n.changeLanguage(normalizeLanguage(me.locale ?? 'en'));
      setUser(me);
      return me;
    } catch (error) {
      log.warn('me_fetch_failed', { reason: String(error) });
      const domainError = mapApiError(error);
      if (PROVISION_ERROR_CODES.has(domainError.code)) {
        showDomainErrorToast(domainError);
      }
      setUser(null);
      return null;
    } finally {
      setIsUserLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const kc = initKeycloak();
    kc.init({
      onLoad: 'check-sso',
      pkceMethod: 'S256',
      checkLoginIframe: false,
      silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
    })
      .then((authenticated) => {
        setKeycloak(kc);
        setIsAuthenticated(authenticated);
        if (authenticated) {
          setIsUserLoading(true);
        }
        setKeycloakInitialized();
      })
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      setUser(null);
      Sentry.setUser(null);
      return;
    }
    void refetchUser();
  }, [isAuthenticated, refetchUser]);

  useEffect(() => {
    if (!user) return;
    Sentry.setUser({
      id: user.id,
      email: user.email,
      username: user.full_name ?? undefined,
    });
  }, [user]);

  const login = useCallback(
    (redirectPath?: string) => {
      postLoginRedirect.current = redirectPath;
      const redirectUri = redirectPath
        ? `${window.location.origin}${redirectPath.startsWith('/') ? redirectPath : `/${redirectPath}`}`
        : `${window.location.origin}/auth/callback`;
      keycloak?.login({ redirectUri });
    },
    [keycloak],
  );

  const logout = useCallback(() => {
    setIsAuthenticated(false);
    setUser(null);
    setIsUserLoading(false);
    Sentry.setUser(null);
    void logoutKeycloakSession();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        keycloak,
        isAuthenticated,
        isLoading,
        isUserLoading,
        user,
        login,
        logout,
        refetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
