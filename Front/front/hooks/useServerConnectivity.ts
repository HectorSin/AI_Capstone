import { useCallback, useEffect, useState } from 'react';

type ConnectivityStatus = 'checking' | 'connected' | 'offline';

type ServerConnectivityState = {
  status: ConnectivityStatus;
  lastCheckedAt?: Date;
  errorMessage?: string;
  checkConnection: () => Promise<void>;
};

const SERVER_URL = 'http://34.158.210.47:8000/';
const REQUEST_TIMEOUT_MS = 5000;

const isServerReachable = (statusCode: number) => statusCode >= 200 && statusCode < 400;

export const useServerConnectivity = (): ServerConnectivityState => {
  const [status, setStatus] = useState<ConnectivityStatus>('checking');
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | undefined>();
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const checkConnection = useCallback(async () => {
    setStatus('checking');
    setErrorMessage(undefined);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(SERVER_URL, {
        method: 'GET',
        signal: controller.signal,
      });

      if (isServerReachable(response.status)) {
        setStatus('connected');
      } else {
        setStatus('offline');
        setErrorMessage(`응답 코드 ${response.status}`);
      }
    } catch (error) {
      setStatus('offline');
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('알 수 없는 오류입니다.');
      }
    } finally {
      clearTimeout(timeoutId);
      setLastCheckedAt(new Date());
    }
  }, []);

  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  return {
    status,
    lastCheckedAt,
    errorMessage,
    checkConnection,
  };
};
