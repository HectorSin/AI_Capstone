import { SectionList, StyleSheet, Text, View, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { useCallback, useMemo } from 'react';

import { FeedCard } from '@/components/FeedCard';
import { getArticleFeed } from '@/utils/api';
import type { FeedItem } from '@/types';
import { FeedErrorState, FeedLoadingState } from '@/components/FeedState';
import { useFeedLoader } from '@/hooks/useFeedLoader';

type FeedSection = {
  title: string;
  data: FeedItem[];
};

export default function HomeScreen() {
  const router = useRouter();
  const feedFetcher = useCallback(async () => {
    const response = await getArticleFeed(0, 20);
    return response.items;
  }, []);

  const { items: feedItems, isLoading, isRefreshing, error, reload, refresh } = useFeedLoader<FeedItem>({
    fetcher: feedFetcher,
    fallbackErrorMessage: '피드를 불러올 수 없습니다',
  });

  const feedSections: FeedSection[] = useMemo(
    () =>
      feedItems.reduce<FeedSection[]>((sections, item) => {
        const lastSection = sections[sections.length - 1];
        if (!lastSection || lastSection.title !== item.date) {
          sections.push({ title: item.date, data: [item] });
        } else {
          lastSection.data.push(item);
        }
        return sections;
      }, []),
    [feedItems]
  );

  const navigateToTopic = (topic: string) => {
    router.push({
      pathname: '/topic/[topic]',
      params: { topic },
    });
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <FeedLoadingState message="피드를 불러오는 중..." />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <FeedErrorState title="피드를 불러올 수 없습니다" message={error} onRetry={reload} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SectionList
        sections={feedSections}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <FeedCard
            title={item.title}
            summary={item.summary}
            imageUri={item.imageUri}
            topic={item.topic}
            onPressCard={() =>
              router.push({
                pathname: '/article/[id]',
                params: { id: item.id },
              })
            }
            onPressImage={() => navigateToTopic(item.topic)}
            onPressTopic={() => navigateToTopic(item.topic)}
          />
        )}
        renderSectionHeader={({ section: { title } }) => (
          <View style={styles.sectionHeader}>
            <View style={styles.sectionDivider} />
            <Text style={styles.sectionHeaderText}>{title}</Text>
            <View style={styles.sectionDivider} />
          </View>
        )}
        stickySectionHeadersEnabled
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={refresh}
            tintColor="#2563eb"
            colors={['#2563eb']}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>아직 피드가 없습니다</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  listContent: {
    paddingBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingBottom: 8,
    paddingHorizontal: 20,
    backgroundColor: '#ffffff',
  },
  sectionHeaderText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  sectionDivider: {
    flex: 1,
    height: 1,
    backgroundColor: '#e5e7eb',
  },
  emptyContainer: {
    paddingVertical: 64,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
  },
});
