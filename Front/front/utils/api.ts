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
