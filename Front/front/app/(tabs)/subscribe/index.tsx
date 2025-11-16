import { SectionList, StyleSheet, Text, View, Pressable, Image, ScrollView, ActivityIndicator, RefreshControl } from 'react-native';
import { useMemo, useState, useCallback, useEffect } from 'react';
import { useRouter } from 'expo-router';

import { FeedCard } from '@/components/FeedCard';
import { getSubscribedArticles } from '@/utils/api';
import { useAuth } from '@/providers/AuthProvider';
import type { FeedItem } from '@/types';

const DEFAULT_AVATAR = 'https://images.unsplash.com/photo-500648767791-00dcc994a43e?auto=format&fit=crop&w=160&q=80';

type FeedSection = {
  title: string;
  data: FeedItem[];
};

const groupFeedByDate = (items: FeedItem[]): FeedSection[] =>
  items.reduce<FeedSection[]>((sections, item) => {
    const lastSection = sections[sections.length - 1];
    if (!lastSection || lastSection.title !== item.date) {
      sections.push({ title: item.date, data: [item] });
    } else {
      lastSection.data.push(item);
    }
    return sections;
  }, []);

export default function SubscribeScreen() {
  const router = useRouter();
  const { token } = useAuth();
  const [selectedTopic, setSelectedTopic] = useState<string>('전체');
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 토픽 옵션 생성 (피드 아이템에서 추출)
  const topicAvatars: Record<string, string> = useMemo(() => {
    return feedItems.reduce((acc, item) => {
      if (!acc[item.topic]) {
        acc[item.topic] = item.imageUri;
      }
      return acc;
    }, {} as Record<string, string>);
  }, [feedItems]);

  const topicOptions = useMemo(() => ['전체', ...Object.keys(topicAvatars)], [topicAvatars]);

  // 토픽 필터링
  const filteredItems = useMemo(() => {
    if (selectedTopic === '전체') {
      return feedItems;
    }
    return feedItems.filter((item) => item.topic === selectedTopic);
  }, [selectedTopic, feedItems]);

  const sections = useMemo(() => groupFeedByDate(filteredItems), [filteredItems]);

  const loadFeed = useCallback(async (isRefresh = false) => {
    if (!token) {
      setError('로그인이 필요합니다');
      setIsLoading(false);
      return;
    }

    try {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);
      const response = await getSubscribedArticles(token, 0, 100); // 충분한 개수 로드
      setFeedItems(response.items);
    } catch (err) {
      console.error('[Subscribe] Failed to load feed:', err);
      setError(err instanceof Error ? err.message : '피드를 불러올 수 없습니다');
      setFeedItems([]);
    } finally {
      if (isRefresh) {
        setIsRefreshing(false);
      } else {
        setIsLoading(false);
      }
    }
  }, [token]);

  const handleRefresh = useCallback(() => {
    loadFeed(true);
  }, [loadFeed]);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  const handleTopicPress = (topic: string) => {
    setSelectedTopic(topic);
  };

  const handleNavigateTopic = (topic: string) => {
    router.push({ pathname: '/topic/[topic]', params: { topic } });
  };

  const renderTopicHeader = useCallback(
    () => (
      <View style={styles.topicHeader}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.topicRow}>
          {topicOptions.map((topic) => {
            const isActive = topic === selectedTopic;
            const avatarUri = topic === '전체' ? DEFAULT_AVATAR : topicAvatars[topic] ?? DEFAULT_AVATAR;
            return (
              <Pressable
                key={topic}
                onPress={() => handleTopicPress(topic)}
                style={({ pressed }) => [
                  styles.topicRadio,
                  isActive && styles.topicRadioActive,
                  pressed && styles.topicRadioPressed,
                ]}
              >
                <Image source={{ uri: avatarUri }} style={[styles.topicAvatar, isActive && styles.topicAvatarActive]} />
                <Text style={[styles.topicLabel, isActive && styles.topicLabelActive]} numberOfLines={1}>
                  {topic}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>
    ),
    [selectedTopic, topicOptions, topicAvatars]
  );

  const handleRenderSectionHeader = ({ section: { title } }: { section: FeedSection }) => (
    <View style={styles.sectionWrapper}>
      <View style={styles.sectionHeader}>
        <View style={styles.sectionDivider} />
        <Text style={styles.sectionHeaderText}>{title}</Text>
        <View style={styles.sectionDivider} />
      </View>
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.container}>
        {renderTopicHeader()}
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.loadingText}>구독 피드를 불러오는 중...</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        {renderTopicHeader()}
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
      {renderTopicHeader()}
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.id}
        renderSectionHeader={handleRenderSectionHeader}
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
            onPressImage={() => handleNavigateTopic(item.topic)}
            onPressTopic={() => handleNavigateTopic(item.topic)}
            showDate={false}
          />
        )}
        stickySectionHeadersEnabled
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor="#2563eb"
            colors={['#2563eb']}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>해당 토픽의 새 소식이 없어요</Text>
            <Text style={styles.emptyBody}>관심 있는 토픽을 구독하면 이곳에서 최신 업데이트를 볼 수 있어요.</Text>
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
  topicHeader: {
    backgroundColor: '#ffffff',
  },
  sectionWrapper: {
    backgroundColor: '#ffffff',
  },
  topicRow: {
    paddingHorizontal: 20,
    paddingBottom: 8,
    gap: 16,
  },
  topicRadio: {
    alignItems: 'center',
    width: 72,
    gap: 6,
    opacity: 0.75,
  },
  topicRadioActive: {
    opacity: 1,
  },
  topicRadioPressed: {
    opacity: 0.6,
  },
  topicAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#e5e7eb',
  },
  topicAvatarActive: {
    borderWidth: 2,
    borderColor: '#2563eb',
  },
  topicLabel: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
  },
  topicLabelActive: {
    color: '#111827',
    fontWeight: '600',
  },
  listContent: {
    paddingBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 20,
    backgroundColor: '#ffffff',
  },
  sectionDivider: {
    flex: 1,
    height: 1,
    backgroundColor: '#e5e7eb',
  },
  sectionHeaderText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  emptyState: {
    alignItems: 'center',
    gap: 12,
    marginTop: 72,
    paddingHorizontal: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
  },
  emptyBody: {
    fontSize: 15,
    color: '#6b7280',
    textAlign: 'center',
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
});
