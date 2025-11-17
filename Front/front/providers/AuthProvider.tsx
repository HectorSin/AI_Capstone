import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  API_BASE_URL,
  fetchNotificationPreference,
  updateNotificationPreference as updateNotificationPreferenceApi,
  NotificationPreferenceDTO,
  NotificationPreferenceUpdatePayload,
  getMyTopics,
  subscribeTopic as subscribeTopicApi,
  unsubscribeTopic as unsubscribeTopicApi,
} from '@/utils/api';
import type { Topic } from '@/types';

type Credentials = {
  email: string;
  password: string;
};

type RegisterPayload = Credentials & {
  nickname: string;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  topic_ids?: string[];
};

type AuthenticatedUser = {
  id: string;
  email: string;
  nickname: string;
  plan: string;
  difficulty_level?: string;
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
  subscribedTopics: Topic[];
  signIn: (credentials: Credentials) => Promise<boolean>;
  signUp: (payload: RegisterPayload) => Promise<boolean>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<boolean>;
  refreshProfile: () => Promise<void>;
  refreshNotificationPreference: () => Promise<void>;
  updateNotificationPreference: (input: NotificationPreferenceInput) => Promise<boolean>;
  updateDifficulty: (difficulty: 'beginner' | 'intermediate' | 'advanced') => Promise<boolean>;
  refreshSubscribedTopics: () => Promise<void>;
  subscribeTopic: (topicId: string) => Promise<boolean>;
  unsubscribeTopic: (topicId: string) => Promise<boolean>;
  isTopicSubscribed: (topicId: string) => boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = '@capstone/authToken';
const DEFAULT_HOUR = 7;
const DEFAULT_MINUTE = 0;
const DEFAULT_WEEKDAY_INDICES = [0, 1, 2, 3, 4];

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
  const [subscribedTopics, setSubscribedTopics] = useState<Topic[]>([]);
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
        difficulty_level: data.difficulty_level,
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

  const fetchAndStoreSubscribedTopics = useCallback(
    async (accessToken: string) => {
      try {
        const topics = await getMyTopics(accessToken);
        setSubscribedTopics(topics);
        return topics;
      } catch (error) {
        console.warn('[Auth] fetchSubscribedTopics failed', error);
        setSubscribedTopics([]);
        return [];
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
        await fetchAndStoreSubscribedTopics(accessToken);
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
    async ({ email, password, nickname, difficulty_level, topic_ids }: RegisterPayload) => {
      try {
        const payload = {
          email,
          password,
          nickname,
          difficulty_level: difficulty_level || 'intermediate',
          topic_ids: topic_ids || [],
        };

        console.log('[Auth] signUp request:', {
          url: `${API_BASE_URL}/auth/register/local`,
          payload: { ...payload, password: '***' },
        });

        const response = await fetch(`${API_BASE_URL}/auth/register/local`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify(payload),
        });

        console.log('[Auth] signUp response status:', response.status);
        console.log('[Auth] signUp response.ok:', response.ok);

        if (!response.ok) {
          const errorText = await response.text();
          console.warn('[Auth] signUp failed - status:', response.status, 'error:', errorText);
          return false;
        }

        console.log('[Auth] Parsing response as JSON...');
        const data = await response.json();
        console.log('[Auth] signUp SUCCESS - user created:', { id: data.id, email: data.email });
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
    setSubscribedTopics([]);
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

  const refreshSubscribedTopics = useCallback(async () => {
    if (!token) return;
    await fetchAndStoreSubscribedTopics(token);
  }, [fetchAndStoreSubscribedTopics, token]);

  const subscribeTopic = useCallback(
    async (topicId: string) => {
      if (!token) {
        console.warn('[Auth] subscribeTopic failed: no token');
        return false;
      }

      console.log('[Auth] subscribeTopic started:', topicId);
      try {
        await subscribeTopicApi(token, topicId);
        console.log('[Auth] subscribeTopicApi success, refreshing topics...');
        const topics = await fetchAndStoreSubscribedTopics(token);
        console.log('[Auth] Topics after subscribe:', topics?.map((t) => ({ id: t.id, name: t.name })));
        return true;
      } catch (error) {
        console.error('[Auth] subscribeTopic error', error);
        // API가 실패했더라도 실제로 서버에 반영되었는지 확인
        const topics = await fetchAndStoreSubscribedTopics(token);
        const isSubscribedNow = topics.some((topic) => topic.id === topicId);
        if (isSubscribedNow) {
          console.warn('[Auth] subscribeTopic recovered: topic appears in my list after error');
          return true;
        }
        return false;
      }
    },
    [fetchAndStoreSubscribedTopics, token]
  );

  const unsubscribeTopic = useCallback(
    async (topicId: string) => {
      if (!token) {
        console.warn('[Auth] unsubscribeTopic failed: no token');
        return false;
      }

      console.log('[Auth] unsubscribeTopic started:', topicId);
      try {
        await unsubscribeTopicApi(token, topicId);
        console.log('[Auth] unsubscribeTopicApi success, refreshing topics...');
        const topics = await fetchAndStoreSubscribedTopics(token);
        console.log('[Auth] Topics after unsubscribe:', topics?.map((t) => ({ id: t.id, name: t.name })));
        return true;
      } catch (error) {
        console.error('[Auth] unsubscribeTopic error', error);
        const topics = await fetchAndStoreSubscribedTopics(token);
        const isStillSubscribed = topics.some((topic) => topic.id === topicId);
        if (!isStillSubscribed) {
          console.warn('[Auth] unsubscribeTopic recovered: topic removed despite API error');
          return true;
        }
        return false;
      }
    },
    [fetchAndStoreSubscribedTopics, token]
  );

  const isTopicSubscribed = useCallback(
    (topicId: string) => {
      const result = subscribedTopics.some((topic) => topic.id === topicId);
      // 디버깅용 로그
      if (result) {
        console.log(`✅ [Auth] Topic ${topicId} IS subscribed`);
      } else {
        console.log(`❌ [Auth] Topic ${topicId} is NOT subscribed`);
      }
      console.log('[Auth] Current subscribed topics:', subscribedTopics.map(t => `${t.name} (${t.id})`).join(', '));
      return result;
    },
    [subscribedTopics]
  );

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

  const updateDifficulty = useCallback(
    async (difficulty: 'beginner' | 'intermediate' | 'advanced') => {
      if (!token) {
        return false;
      }

      try {
        console.log('[Auth] Updating difficulty to:', difficulty);

        const response = await fetch(`${API_BASE_URL}/users/me`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            difficulty_level: difficulty,
          }),
        });

        console.log('[Auth] Update difficulty response status:', response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.warn('[Auth] updateDifficulty failed:', response.status, errorText);
          return false;
        }

        const data = await response.json();
        console.log('[Auth] Difficulty updated successfully:', data.difficulty_level);

        // 프로필 새로고침
        await fetchProfile(token);
        return true;
      } catch (error) {
        console.warn('[Auth] updateDifficulty error', error);
        return false;
      }
    },
    [fetchProfile, token]
  );

  useEffect(() => {
    (async () => {
      try {
        const storedToken = await AsyncStorage.getItem(TOKEN_STORAGE_KEY);
        if (storedToken) {
          setToken(storedToken);
          await fetchProfile(storedToken);
          await fetchAndStorePreference(storedToken);
          await fetchAndStoreSubscribedTopics(storedToken);
        }
      } catch (error) {
        console.warn('[Auth] failed to hydrate token', error);
      } finally {
        setIsHydrated(true);
      }
    })();
  }, [fetchAndStorePreference, fetchAndStoreSubscribedTopics, fetchProfile]);

  const value = useMemo(
    () => ({
      isSignedIn: Boolean(token && user),
      user,
      token,
      notificationPreference,
      subscribedTopics,
      signIn,
      signUp,
      signOut,
      deleteAccount,
      refreshProfile,
      refreshNotificationPreference,
      updateNotificationPreference,
      updateDifficulty,
      refreshSubscribedTopics,
      subscribeTopic,
      unsubscribeTopic,
      isTopicSubscribed,
    }),
    [
      token,
      user,
      notificationPreference,
      subscribedTopics,
      signIn,
      signUp,
      signOut,
      deleteAccount,
      refreshProfile,
      refreshNotificationPreference,
      updateNotificationPreference,
      updateDifficulty,
      refreshSubscribedTopics,
      subscribeTopic,
      unsubscribeTopic,
      isTopicSubscribed,
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
