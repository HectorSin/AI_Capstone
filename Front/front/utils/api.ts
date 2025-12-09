export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://api.snackcast.shop';

let authTokenLoader: (() => Promise<string | null>) | null = null;

export function registerAuthTokenLoader(loader: () => Promise<string | null>) {
  authTokenLoader = loader;
}

async function getAuthToken(): Promise<string | null> {
  if (!authTokenLoader) return null;
  return authTokenLoader();
}

export async function getAuthTokenValue(): Promise<string | null> {
  return getAuthToken();
}

export async function checkAvailability(
  endpoint: 'check-email' | 'check-nickname',
  value: string,
  signal?: AbortSignal
): Promise<boolean> {
  const paramName = endpoint === 'check-email' ? 'email' : 'nickname';
  const url = `${API_BASE_URL}/auth/${endpoint}?${paramName}=${encodeURIComponent(value)}`;

  console.log('[API] checkAvailability:', { endpoint, value, url });

  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    signal,
  });

  console.log('[API] checkAvailability response:', response.status);

  if (!response.ok) {
    const text = await response.text();
    console.error(`[API] Failed to check ${endpoint}:`, response.status, text);
    throw new Error(`Failed to check ${endpoint}: ${response.status}`);
  }

  const data = await response.json();
  console.log('[API] checkAvailability data:', data);
  return Boolean(data?.available);
}

export type NotificationPreferenceDTO = {
  id: string;
  allowed: boolean;
  time_enabled: boolean;
  hour: number | null;
  minute: number | null;
  days_of_week: number[];
  prompted: boolean;
  created_at: string;
  updated_at: string;
};

export type NotificationPreferenceUpdatePayload = {
  allowed: boolean;
  time_enabled: boolean;
  hour: number | null;
  minute: number | null;
  days_of_week: number[];
  prompted: boolean;
};

export async function fetchNotificationPreference(token: string): Promise<NotificationPreferenceDTO> {
  const response = await fetch(`${API_BASE_URL}/users/me/notification-preference`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch notification preference: ${response.status}`);
  }

  return response.json();
}

export async function updateNotificationPreference(
  token: string,
  payload: NotificationPreferenceUpdatePayload
): Promise<NotificationPreferenceDTO> {
  const response = await fetch(`${API_BASE_URL}/users/me/notification-preference`, {
    method: 'PUT',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to update notification preference: ${response.status}`);
  }

  return response.json();
}

// ============================================================
// Article Feed API (Phase 5 - 프론트엔드 연동)
// ============================================================

import type { FeedItem } from '@/types';

export type ArticleFeedResponse = {
  items: FeedItem[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
};

/**
 * Home 피드 조회 (전체 Article)
 */
export async function getArticleFeed(skip: number = 0, limit: number = 20): Promise<ArticleFeedResponse> {
  const response = await fetch(`${API_BASE_URL}/articles/feed?skip=${skip}&limit=${limit}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch article feed: ${response.status}`);
  }

  return response.json();
}

/**
 * Subscribe 피드 조회 (구독 토픽의 Article)
 * @param token - 인증 토큰 (필수)
 */
export async function getSubscribedArticles(
  token: string,
  skip: number = 0,
  limit: number = 20
): Promise<ArticleFeedResponse> {
  const response = await fetch(`${API_BASE_URL}/articles/subscribed?skip=${skip}&limit=${limit}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch subscribed articles: ${response.status}`);
  }

  return response.json();
}

/**
 * Article 상세 조회
 * @param articleId - Article ID
 * @param token - 인증 토큰 (선택적). 제공되면 사용자 난이도에 맞는 콘텐츠 반환
 */
export async function getArticleById(articleId: string, token?: string | null): Promise<FeedItem> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };

  // 토큰이 있으면 Authorization 헤더 추가
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/articles/${articleId}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch article: ${response.status}`);
  }

  return response.json();
}

/**
 * Topic 이름으로 Topic 정보 조회
 */
export async function getTopicByName(topicName: string): Promise<Topic> {
  const response = await fetch(
    `${API_BASE_URL}/topics/by-name/${encodeURIComponent(topicName)}`,
    {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch topic: ${response.status}`);
  }

  return response.json();
}

/**
 * Topic 기반 Article 조회
 */
export async function getArticlesByTopic(
  topicName: string,
  skip: number = 0,
  limit: number = 20
): Promise<ArticleFeedResponse> {
  const response = await fetch(
    `${API_BASE_URL}/topics/by-name/${encodeURIComponent(topicName)}/articles?skip=${skip}&limit=${limit}`,
    {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch articles by topic: ${response.status}`);
  }

  return response.json();
}

// ============================================================
// Topic 구독 관리 API
// ============================================================

import type { Topic } from '@/types';
import type { DailyPodcastSummary } from '@/types/podcast';

/**
 * 내가 구독 중인 토픽 목록 조회
 */
export async function getMyTopics(token: string): Promise<Topic[]> {
  console.log('[API] getMyTopics request');

  const response = await fetch(`${API_BASE_URL}/users/me/topics`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  console.log('[API] getMyTopics response:', { status: response.status, ok: response.ok });

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unable to read error');
    console.error('[API] getMyTopics failed:', { status: response.status, error: errorText });
    throw new Error(`Failed to fetch my topics: ${response.status}`);
  }

  const data = await response.json();
  console.log('[API] getMyTopics success:', { count: data.length, topics: data.map((t: Topic) => ({ id: t.id, name: t.name })) });
  return data;
}

/**
 * 토픽 구독 추가
 */
export async function subscribeTopic(token: string, topicId: string): Promise<void> {
  console.log('[API] subscribeTopic request:', { topicId, url: `${API_BASE_URL}/users/me/topics/${topicId}` });

  const response = await fetch(`${API_BASE_URL}/users/me/topics/${topicId}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  console.log('[API] subscribeTopic response:', { status: response.status, ok: response.ok });

  let rawBody = '';
  try {
    rawBody = await response.text();
  } catch (error) {
    rawBody = '';
  }

  if (!response.ok) {
    const errorText = rawBody || 'Unable to read error';
    console.error('[API] subscribeTopic failed:', { status: response.status, error: errorText });
    throw new Error(`Failed to subscribe topic: ${response.status} - ${errorText}`);
  }

  if (rawBody) {
    try {
      const data = JSON.parse(rawBody);
      console.log('[API] subscribeTopic success:', data);
    } catch {
      console.log('[API] subscribeTopic success (non-JSON body):', rawBody);
    }
  } else {
    console.log('[API] subscribeTopic success (empty body)');
  }
}

/**
 * 토픽 구독 취소
 */
export async function unsubscribeTopic(token: string, topicId: string): Promise<void> {
  console.log('[API] unsubscribeTopic request:', { topicId, url: `${API_BASE_URL}/users/me/topics/${topicId}` });

  const response = await fetch(`${API_BASE_URL}/users/me/topics/${topicId}`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  console.log('[API] unsubscribeTopic response:', { status: response.status, ok: response.ok });

  let rawBody = '';
  try {
    rawBody = await response.text();
  } catch (error) {
    rawBody = '';
  }

  if (!response.ok) {
    const errorText = rawBody || 'Unable to read error';
    console.error('[API] unsubscribeTopic failed:', { status: response.status, error: errorText });
    throw new Error(`Failed to unsubscribe topic: ${response.status} - ${errorText}`);
  }

  console.log('[API] unsubscribeTopic success');
}

// ============================================================
// Podcasts / Archive API
// ============================================================
export async function getDailyPodcasts(startDate?: string, endDate?: string): Promise<DailyPodcastSummary[]> {
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  const query = params.toString();
  const url = `${API_BASE_URL}/podcasts/daily${query ? `?${query}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${await getAuthToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch daily podcasts: ${response.status}`);
  }

  return response.json();
}

// ============================================================
// Token Refresh API
// ============================================================

/**
 * Refresh Token으로 새로운 Access Token 발급
 * @param refreshToken Refresh Token
 * @returns 새로운 Access Token과 Refresh Token
 */
export async function refreshAccessToken(refreshToken: string): Promise<{ access_token: string; refresh_token: string }> {
  console.log('[API] refreshAccessToken request');

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  console.log('[API] refreshAccessToken response:', { status: response.status, ok: response.ok });

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unable to read error');
    console.error('[API] refreshAccessToken failed:', { status: response.status, error: errorText });
    throw new Error(`Failed to refresh token: ${response.status}`);
  }

  const data = await response.json();
  console.log('[API] refreshAccessToken success');
  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
  };
}
