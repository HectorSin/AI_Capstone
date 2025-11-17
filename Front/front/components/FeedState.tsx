import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

type FeedLoadingStateProps = {
  message: string;
};

type FeedErrorStateProps = {
  title: string;
  message?: string | null;
  onRetry?: () => void;
  retryLabel?: string;
};

export function FeedLoadingState({ message }: FeedLoadingStateProps) {
  return (
    <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color="#2563eb" />
      <Text style={styles.loadingText}>{message}</Text>
    </View>
  );
}

export function FeedErrorState({ title, message, onRetry, retryLabel = '다시 시도' }: FeedErrorStateProps) {
  return (
    <View style={styles.errorContainer}>
      <Text style={styles.errorTitle}>{title}</Text>
      {message ? <Text style={styles.errorMessage}>{message}</Text> : null}
      {onRetry ? (
        <Pressable onPress={onRetry} hitSlop={8}>
          <Text style={styles.errorHint}>{retryLabel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: '#6b7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    gap: 12,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
  },
  errorMessage: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  errorHint: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2563eb',
    marginTop: 8,
  },
});
