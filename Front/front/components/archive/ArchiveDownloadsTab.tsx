import { useCallback, useState } from 'react';
import { Alert, FlatList, RefreshControl, StyleSheet, Text, View, Pressable } from 'react-native';
import { useFocusEffect } from 'expo-router';

import { listDownloadedPlaylists, removeDownloadedPlaylist, type DownloadedPlaylist } from '@/utils/archiveStorage';
import { formatDuration } from '@/utils/format';
import { useAudioPlayer } from '@/providers/AudioPlayerProvider';

export function ArchiveDownloadsTab() {
  const [items, setItems] = useState<DownloadedPlaylist[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { loadPlaylist, currentPlaylist } = useAudioPlayer();

  const loadDownloads = useCallback(async () => {
    const downloads = await listDownloadedPlaylists();
    setItems(downloads);
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadDownloads();
    }, [loadDownloads])
  );

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadDownloads();
    setIsRefreshing(false);
  }, [loadDownloads]);

  const handleDelete = useCallback(
    (id: string) => {
      Alert.alert('삭제', '다운로드한 팟캐스트를 삭제할까요?', [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            await removeDownloadedPlaylist(id);
            loadDownloads();
          },
        },
      ]);
    },
    [loadDownloads]
  );

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.listContent}
      refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} tintColor="#2563eb" colors={['#2563eb']} />}
      renderItem={({ item }) => (
        <DownloadCard
          playlist={item}
          onDelete={() => handleDelete(item.id)}
          onPlay={() => loadPlaylist(item)}
        />
      )}
      ListEmptyComponent={
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>다운로드한 팟캐스트가 없어요</Text>
          <Text style={styles.emptyBody}>보관함에서 다운로드하면 이곳에서 다시 재생할 수 있어요.</Text>
        </View>
      }
      ListFooterComponent={<View style={{ height: currentPlaylist ? 280 : 0 }} />}
    />
  );
}

function DownloadCard({ playlist, onDelete, onPlay }: { playlist: DownloadedPlaylist; onDelete: () => void; onPlay: () => void }) {
  const difficultyLabel = playlist.difficulty;

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{playlist.date}</Text>
        <View style={styles.difficultyBadge}>
          <Text style={styles.difficultyText}>{difficultyLabel}</Text>
        </View>
      </View>
      <Text style={styles.cardSubtitle}>
        기사 {playlist.segments.length}개 · {playlist.topics.join(', ')}
      </Text>
      <Text style={styles.cardDuration}>{formatDuration(playlist.totalDurationSeconds)}</Text>
      <View style={styles.cardActions}>
        <Pressable style={styles.cardButton} onPress={onPlay}>
          <Text style={styles.cardButtonText}>재생</Text>
        </Pressable>
        <Pressable onPress={onDelete} style={[styles.cardButton, styles.deleteButton]}>
          <Text style={[styles.cardButtonText, styles.deleteButtonText]}>삭제</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
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
    textAlign: 'center',
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
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    flex: 1,
  },
  difficultyBadge: {
    backgroundColor: '#eff6ff',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2563eb',
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#4b5563',
    marginTop: 4,
  },
  cardDuration: {
    fontSize: 14,
    color: '#2563eb',
    marginTop: 8,
    fontWeight: '600',
  },
  cardActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  cardButton: {
    flex: 1,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    backgroundColor: '#2563eb',
  },
  cardButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  deleteButton: {
    backgroundColor: '#fef2f2',
  },
  deleteButtonText: {
    color: '#dc2626',
  },
});
