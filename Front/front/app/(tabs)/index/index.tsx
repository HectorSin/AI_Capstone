import { SectionList, StyleSheet, Text, View, ActivityIndicator, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { useEffect, useState, useCallback } from 'react';

import { FeedCard } from '@/components/FeedCard';
import { ServerConnectivityBanner } from '@/components/ServerConnectivityBanner';
import { getArticleFeed } from '@/utils/api';
import type { FeedItem } from '@/types';

type FeedSection = {
  title: string;
  data: FeedItem[];
};

export default function HomeScreen() {
  const router = useRouter();
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFeed = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);
      const response = await getArticleFeed(0, 20);
      setFeedItems(response.items);
    } catch (err) {
      console.error('[Home] Failed to load feed:', err);
      setError(err instanceof Error ? err.message : '피드를 불러올 수 없습니다');
      // 에러 발생 시 빈 배열로 설정 (fallback)
      setFeedItems([]);
    } finally {
      if (isRefresh) {
        setIsRefreshing(false);
      } else {
        setIsLoading(false);
      }
    }
  }, []);

  const handleRefresh = useCallback(() => {
    loadFeed(true);
  }, [loadFeed]);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  const feedSections: FeedSection[] = feedItems.reduce<FeedSection[]>((sections, item) => {
    const lastSection = sections[sections.length - 1];
    if (!lastSection || lastSection.title !== item.date) {
      sections.push({ title: item.date, data: [item] });
    } else {
      lastSection.data.push(item);
    }
    return sections;
  }, []);

  const navigateToKeyword = (keyword: string) => {
    router.push({
      pathname: '/keyword/[keyword]',
      params: { keyword },
    });
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <ServerConnectivityBanner />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.loadingText}>피드를 불러오는 중...</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <ServerConnectivityBanner />
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>피드를 불러올 수 없습니다</Text>
          <Text style={styles.errorMessage}>{error}</Text>
          <Text style={styles.errorHint} onPress={loadFeed}>
            다시 시도
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ServerConnectivityBanner />
      <SectionList
        sections={feedSections}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <FeedCard
            title={item.title}
            summary={item.summary}
            imageUri={item.imageUri}
            keyword={item.keyword}
            onPressCard={() =>
              router.push({
                pathname: '/article/[id]',
                params: { id: item.id },
              })
            }
            onPressImage={() => navigateToKeyword(item.keyword)}
            onPressKeyword={() => navigateToKeyword(item.keyword)}
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
            onRefresh={handleRefresh}
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
  emptyContainer: {
    paddingVertical: 64,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
  },
});
