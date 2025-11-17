import { useCallback, useMemo, useState } from 'react';
import { Alert, SectionList, StyleSheet, Text, View, RefreshControl, Pressable } from 'react-native';

import { FeedErrorState, FeedLoadingState } from '@/components/FeedState';
import { useFeedLoader } from '@/hooks/useFeedLoader';
import { getDailyPodcasts } from '@/utils/api';
import type { DailyPodcastSummary } from '@/types/podcast';
import { formatDuration } from '@/utils/format';
import { downloadPlaylist } from '@/utils/archiveStorage';
import { useAuth } from '@/providers/AuthProvider';

export function ArchiveRemoteTab() {
  const { isSignedIn } = useAuth();
  const [downloadingDate, setDownloadingDate] = useState<string | null>(null);

  const fetcher = useCallback(async () => {
    if (!isSignedIn) {
      throw new Error('로그인이 필요합니다');
    }
    const response = await getDailyPodcasts();
    return response;
  }, [isSignedIn]);

  const { items, isLoading, error, reload, refresh, isRefreshing } = useFeedLoader<DailyPodcastSummary>({
    fetcher,
    fallbackErrorMessage: '보관함을 불러올 수 없습니다',
  });

  const sections = useMemo(() => items.map((summary) => ({ title: summary.date, data: [summary] })), [items]);

  const handleDownload = useCallback(
    async (summary: DailyPodcastSummary) => {
      if (downloadingDate) {
        return;
      }
      setDownloadingDate(summary.date);
      try {
        await downloadPlaylist(summary);
        Alert.alert('다운로드 완료', `${summary.date} 팟캐스트가 저장되었습니다.`);
      } catch (err) {
        console.warn('[Archive] download failed', err);
        Alert.alert('에러', '다운로드 중 문제가 발생했습니다.');
      } finally {
        setDownloadingDate(null);
      }
    },
    [downloadingDate]
  );

  if (!isSignedIn) {
    return (
      <View style={styles.stateContainer}>
        <Text style={styles.noticeTitle}>로그인이 필요합니다</Text>
        <Text style={styles.noticeBody}>로그인 후 구독 중인 토픽의 보관함을 확인할 수 있어요.</Text>
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={styles.stateContainer}>
        <FeedLoadingState message="보관함을 불러오는 중..." />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.stateContainer}>
        <FeedErrorState title="보관함을 불러올 수 없습니다" message={error} onRetry={reload} />
      </View>
    );
  }

  return (
    <SectionList
      sections={sections}
      keyExtractor={(item) => item.date}
      contentContainerStyle={styles.listContent}
      renderItem={({ item }) => (
        <RemoteCard
          summary={item}
          isDownloading={downloadingDate === item.date}
          onDownload={() => handleDownload(item)}
        />
      )}
      refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} tintColor="#2563eb" colors={['#2563eb']} />}
      ListEmptyComponent={
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>보관된 팟캐스트가 없어요</Text>
          <Text style={styles.emptyBody}>다운로드 버튼으로 하루치 팟캐스트를 저장해 보세요.</Text>
        </View>
      }
    />
  );
}

type RemoteCardProps = {
  summary: DailyPodcastSummary;
  isDownloading: boolean;
  onDownload: () => void;
};

function RemoteCard({ summary, isDownloading, onDownload }: RemoteCardProps) {
  const totalDuration = formatDuration(summary.total_duration_seconds);
  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{summary.date}</Text>
        <Text style={styles.cardDuration}>{totalDuration}</Text>
      </View>
      <Text style={styles.cardSubtitle}>기사 {summary.article_count}개 · {summary.topics.join(', ')}</Text>
      <Pressable
        onPress={onDownload}
        disabled={isDownloading}
        style={({ pressed }) => [styles.downloadButton, pressed && styles.downloadButtonPressed, isDownloading && styles.downloadButtonDisabled]}
      >
        <Text style={styles.downloadLabel}>{isDownloading ? '다운로드 중...' : '다운로드'}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  stateContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  noticeTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  noticeBody: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
    gap: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  emptyBody: {
    fontSize: 14,
    color: '#6b7280',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  cardDuration: {
    fontSize: 14,
    color: '#6b7280',
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#4b5563',
    marginTop: 4,
  },
  downloadButton: {
    marginTop: 12,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#2563eb',
    alignItems: 'center',
  },
  downloadButtonDisabled: {
    opacity: 0.6,
  },
  downloadButtonPressed: {
    opacity: 0.8,
  },
  downloadLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
});
