import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  API_BASE_URL,
  fetchNotificationPreference,
  updateNotificationPreference as updateNotificationPreferenceApi,
  NotificationPreferenceDTO,
  NotificationPreferenceUpdatePayload,
} from '@/utils/api';

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

type NotificationPreferenceState = {
  id: string;
  allowed: boolean;
  timeEnabled: boolean;
  hour: number | null;
  minute: number | null;
  daysOfWeek: number[];
  prompted: boolean;
  createdAt: string;
  updatedAt: string;
};

type NotificationPreferenceInput = {
  allowed: boolean;
  timeEnabled: boolean;
  hour: number | null;
  minute: number | null;
  daysOfWeek: number[];
  prompted: boolean;
};

type AuthContextValue = {
  isSignedIn: boolean;
  user: AuthenticatedUser | null;
  token: string | null;
  notificationPreference: NotificationPreferenceState | null;
  signIn: (credentials: Credentials) => Promise<boolean>;
  signUp: (payload: RegisterPayload) => Promise<boolean>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<boolean>;
  refreshProfile: () => Promise<void>;
  refreshNotificationPreference: () => Promise<void>;
  updateNotificationPreference: (input: NotificationPreferenceInput) => Promise<boolean>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = '@capstone/authToken';
const DEFAULT_HOUR = 7;
const DEFAULT_MINUTE = 0;
const DEFAULT_WEEKDAY_INDICES = [0, 1, 2, 3, 4];

// 개발 모드: 로그인 우회 (true로 설정하면 로그인 없이 바로 접근 가능)
const SKIP_AUTH = true;

type AuthProviderProps = {
  children: ReactNode;
};

const mapPreferenceFromDto = (dto: NotificationPreferenceDTO): NotificationPreferenceState => ({
  id: dto.id,
  allowed: dto.allowed,
  timeEnabled: dto.time_enabled,
  hour: dto.hour,
  minute: dto.minute,
  daysOfWeek: dto.days_of_week ?? [],
  prompted: dto.prompted,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
});

const buildUpdatePayload = (input: NotificationPreferenceInput): NotificationPreferenceUpdatePayload => ({
  allowed: input.allowed,
  time_enabled: input.timeEnabled,
  hour: input.hour,
  minute: input.minute,
  days_of_week: input.daysOfWeek,
  prompted: input.prompted,
});

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [notificationPreference, setNotificationPreference] = useState<NotificationPreferenceState | null>(null);
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

  const fetchAndStorePreference = useCallback(
    async (accessToken: string) => {
      try {
        const dto = await fetchNotificationPreference(accessToken);
        const mapped = mapPreferenceFromDto(dto);
        setNotificationPreference(mapped);
        return mapped;
      } catch (error) {
        console.warn('[Auth] fetchNotificationPreference failed', error);
        setNotificationPreference(null);
        return null;
      }
    },
    []
  );

  const persistToken = useCallback(async (accessToken: string | null) => {
    setToken(accessToken);
    if (accessToken) {
      await AsyncStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
    } else {
      await AsyncStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  }, []);

  const applyInitialNotificationChoice = useCallback(
    async (accessToken: string, allow: boolean) => {
      try {
        const payload: NotificationPreferenceInput = allow
          ? {
              allowed: true,
              timeEnabled: true,
              hour: DEFAULT_HOUR,
              minute: DEFAULT_MINUTE,
              daysOfWeek: DEFAULT_WEEKDAY_INDICES,
              prompted: true,
            }
          : {
              allowed: false,
              timeEnabled: false,
              hour: null,
              minute: null,
              daysOfWeek: [],
              prompted: true,
            };

        const dto = await updateNotificationPreferenceApi(accessToken, buildUpdatePayload(payload));
        setNotificationPreference(mapPreferenceFromDto(dto));
      } catch (error) {
        console.warn('[Auth] applyInitialNotificationChoice failed', error);
      }
    },
    []
  );

  const maybePromptNotificationConsent = useCallback(
    (pref: NotificationPreferenceState | null, accessToken: string) => {
      if (!pref || pref.prompted) {
        return;
      }

      Alert.alert('알림 설정', '알림을 받아보시겠어요? (기본: 평일 오전 7시)', [
        {
          text: '허용 안 함',
          style: 'cancel',
          onPress: () => applyInitialNotificationChoice(accessToken, false),
        },
        {
          text: '허용',
          onPress: () => applyInitialNotificationChoice(accessToken, true),
        },
      ]);
    },
    [applyInitialNotificationChoice]
  );

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
        const pref = await fetchAndStorePreference(accessToken);
        maybePromptNotificationConsent(pref, accessToken);
        return true;
      } catch (error) {
        console.warn('[Auth] signIn error', error);
        return false;
      }
    },
    [fetchAndStorePreference, fetchProfile, maybePromptNotificationConsent, persistToken]
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
    setNotificationPreference(null);
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

  const refreshNotificationPreference = useCallback(async () => {
    if (!token) return;
    await fetchAndStorePreference(token);
  }, [fetchAndStorePreference, token]);

  const updateNotificationPreference = useCallback(
    async (input: NotificationPreferenceInput) => {
      if (!token) {
        return false;
      }

      try {
        const dto = await updateNotificationPreferenceApi(token, buildUpdatePayload(input));
        setNotificationPreference(mapPreferenceFromDto(dto));
        return true;
      } catch (error) {
        console.warn('[Auth] updateNotificationPreference error', error);
        return false;
      }
    },
    [token]
  );

  useEffect(() => {
    (async () => {
      try {
        if (SKIP_AUTH) {
          // 개발 모드: 더미 토큰과 유저 정보 설정
          const dummyToken = 'dev-skip-auth-token';
          const dummyUser: AuthenticatedUser = {
            id: 'dev-user-id',
            email: 'dev@example.com',
            nickname: '개발자',
            plan: 'free',
            createdAt: new Date().toISOString(),
          };
          setToken(dummyToken);
          setUser(dummyUser);
          console.log('[Auth] Development mode: Skipping authentication');
        } else {
          const storedToken = await AsyncStorage.getItem(TOKEN_STORAGE_KEY);
          if (storedToken) {
            setToken(storedToken);
            await fetchProfile(storedToken);
            await fetchAndStorePreference(storedToken);
          }
        }
      } catch (error) {
        console.warn('[Auth] failed to hydrate token', error);
      } finally {
        setIsHydrated(true);
      }
    })();
  }, [fetchAndStorePreference, fetchProfile]);

  const value = useMemo(
    () => ({
      isSignedIn: Boolean(token && user),
      user,
      token,
      notificationPreference,
      signIn,
      signUp,
      signOut,
      deleteAccount,
      refreshProfile,
      refreshNotificationPreference,
      updateNotificationPreference,
    }),
    [
      token,
      user,
      notificationPreference,
      signIn,
      signUp,
      signOut,
      deleteAccount,
      refreshProfile,
      refreshNotificationPreference,
      updateNotificationPreference,
    ]
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
