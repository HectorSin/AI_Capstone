export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function checkAvailability(
  endpoint: 'check-email' | 'check-nickname',
  value: string,
  signal?: AbortSignal
): Promise<boolean> {
  const url = new URL(`/auth/${endpoint}`, API_BASE_URL);
  const paramName = endpoint === 'check-email' ? 'email' : 'nickname';
  url.searchParams.set(paramName, value);

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: { Accept: 'application/json' },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Failed to check ${endpoint}: ${response.status}`);
  }

  const data = await response.json();
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
