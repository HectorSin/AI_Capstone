export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://35.216.97.52:8000';

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
 */
export async function getArticleById(articleId: string): Promise<FeedItem> {
  const response = await fetch(`${API_BASE_URL}/articles/${articleId}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
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

/**
 * 내가 구독 중인 토픽 목록 조회
 */
export async function getMyTopics(token: string): Promise<Topic[]> {
  const response = await fetch(`${API_BASE_URL}/users/me/topics`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch my topics: ${response.status}`);
  }

  return response.json();
}

/**
 * 토픽 구독 추가
 */
export async function subscribeTopic(token: string, topicId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/users/me/topics/${topicId}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to subscribe topic: ${response.status}`);
  }
}

/**
 * 토픽 구독 취소
 */
export async function unsubscribeTopic(token: string, topicId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/users/me/topics/${topicId}`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to unsubscribe topic: ${response.status}`);
  }
}
