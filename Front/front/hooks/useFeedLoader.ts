import { useCallback, useEffect, useState } from 'react';

type UseFeedLoaderOptions<T> = {
  fetcher: () => Promise<T[]>;
  fallbackErrorMessage?: string;
};

type UseFeedLoaderResult<T> = {
  items: T[];
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  reload: () => Promise<void>;
  refresh: () => Promise<void>;
};

export function useFeedLoader<T>({
  fetcher,
  fallbackErrorMessage = '데이터를 불러올 수 없습니다',
}: UseFeedLoaderOptions<T>): UseFeedLoaderResult<T> {
  const [items, setItems] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (isRefresh: boolean = false) => {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }

      try {
        const responseItems = await fetcher();
        setItems(responseItems);
        setError(null);
      } catch (err) {
        console.error('[useFeedLoader] Failed to load feed:', err);
        setItems([]);
        setError(err instanceof Error ? err.message : fallbackErrorMessage);
      } finally {
        if (isRefresh) {
          setIsRefreshing(false);
        } else {
          setIsLoading(false);
        }
      }
    },
    [fetcher, fallbackErrorMessage]
  );

  useEffect(() => {
    load();
  }, [load]);

  const reload = useCallback(() => load(false), [load]);
  const refresh = useCallback(() => load(true), [load]);

  return {
    items,
    isLoading,
    isRefreshing,
    error,
    reload,
    refresh,
  };
}
