import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { useServerConnectivity } from '@/hooks/useServerConnectivity';

const STATUS_COPY = {
  checking: {
    label: '서버 연결 상태 확인 중...',
    backgroundColor: '#fef3c7',
    textColor: '#92400e',
  },
  connected: {
    label: '서버와 연결되었습니다.',
    backgroundColor: '#dcfce7',
    textColor: '#166534',
  },
  offline: {
    label: '서버와 연결할 수 없습니다.',
    backgroundColor: '#fee2e2',
    textColor: '#b91c1c',
  },
} as const;

export const ServerConnectivityBanner = () => {
  const { status, lastCheckedAt, errorMessage, checkConnection } = useServerConnectivity();
  const { label, backgroundColor, textColor } = STATUS_COPY[status];

  return (
    <Pressable
      onPress={checkConnection}
      disabled={status === 'checking'}
      style={[styles.container, { backgroundColor }]}
    >
      <View style={styles.row}>
        {status === 'checking' ? (
          <ActivityIndicator color={textColor} size="small" />
        ) : (
          <View style={[styles.statusDot, { backgroundColor: textColor }]} />
        )}
        <View style={styles.textWrapper}>
          <Text style={[styles.label, { color: textColor }]}>{label}</Text>
          {status === 'offline' && errorMessage ? (
            <Text style={[styles.meta, { color: textColor }]}>{errorMessage}</Text>
          ) : null}
          {lastCheckedAt ? (
            <Text style={[styles.meta, { color: textColor }]}>마지막 확인: {lastCheckedAt.toLocaleTimeString()}</Text>
          ) : null}
          {status !== 'checking' ? (
            <Text style={[styles.meta, { color: textColor }]}>탭하여 다시 확인</Text>
          ) : null}
        </View>
      </View>
    </Pressable>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginHorizontal: 20,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  textWrapper: {
    flex: 1,
    gap: 4,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
  },
  meta: {
    fontSize: 12,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
});
