import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { API_BASE_URL } from '@/utils/api';

type Credentials = {
  email: string;
  password: string;
};

type RegisterPayload = Credentials & {
  nickname: string;
};

type AuthenticatedUser = {
  id: string;
  email: string;
  nickname: string;
  plan: string;
  createdAt: string;
};

type AuthContextValue = {
  isSignedIn: boolean;
  user: AuthenticatedUser | null;
  token: string | null;
  signIn: (credentials: Credentials) => Promise<boolean>;
  signUp: (payload: RegisterPayload) => Promise<boolean>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<boolean>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = '@capstone/authToken';

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  const fetchProfile = useCallback(async (accessToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }

      const data = await response.json();
      setUser({
        id: data.id,
        email: data.email,
        nickname: data.nickname,
        plan: data.plan,
        createdAt: data.created_at ?? data.createdAt,
      });
    } catch (error) {
      console.warn('[Auth] fetchProfile failed', error);
      setUser(null);
    }
  }, []);

  const persistToken = useCallback(async (accessToken: string | null) => {
    setToken(accessToken);
    if (accessToken) {
      await AsyncStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
    } else {
      await AsyncStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  }, []);

  const signIn = useCallback(
    async ({ email, password }: Credentials) => {
      try {
        const formBody = new URLSearchParams({
          username: email.trim(),
          password,
        }).toString();

        const response = await fetch(`${API_BASE_URL}/auth/login/local`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            Accept: 'application/json',
          },
          body: formBody,
        });

        if (!response.ok) {
          console.warn('[Auth] signIn failed', response.status, await response.text());
          return false;
        }

        const { access_token: accessToken } = await response.json();
        if (!accessToken) {
          console.warn('[Auth] signIn response missing token');
          return false;
        }

        await persistToken(accessToken);
        await fetchProfile(accessToken);
        return true;
      } catch (error) {
        console.warn('[Auth] signIn error', error);
        return false;
      }
    },
    [fetchProfile, persistToken]
  );

  const signUp = useCallback(
    async ({ email, password, nickname }: RegisterPayload) => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/register/local`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({ email, password, nickname }),
        });

        if (!response.ok) {
          console.warn('[Auth] signUp failed', response.status, await response.text());
          return false;
        }

        return true;
      } catch (error) {
        console.warn('[Auth] signUp error', error);
        return false;
      }
    },
    []
  );

  const signOut = useCallback(async () => {
    await persistToken(null);
    setUser(null);
  }, [persistToken]);

  const deleteAccount = useCallback(async () => {
    if (!token) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
      });

      if (response.status !== 204) {
        console.warn('[Auth] deleteAccount failed', response.status, await response.text().catch(() => ''));
        return false;
      }

      await signOut();
      return true;
    } catch (error) {
      console.warn('[Auth] deleteAccount error', error);
      return false;
    }
  }, [signOut, token]);

  const refreshProfile = useCallback(async () => {
    if (!token) return;
    await fetchProfile(token);
  }, [fetchProfile, token]);

  useEffect(() => {
    (async () => {
      try {
        const storedToken = await AsyncStorage.getItem(TOKEN_STORAGE_KEY);
        if (storedToken) {
          setToken(storedToken);
          await fetchProfile(storedToken);
        }
      } catch (error) {
        console.warn('[Auth] failed to hydrate token', error);
      } finally {
        setIsHydrated(true);
      }
    })();
  }, [fetchProfile]);

  const value = useMemo(
    () => ({
      isSignedIn: Boolean(token && user),
      user,
      token,
      signIn,
      signUp,
      signOut,
      deleteAccount,
      refreshProfile,
    }),
    [token, user, signIn, signUp, signOut, deleteAccount, refreshProfile]
  );

  if (!isHydrated) {
    return null;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
