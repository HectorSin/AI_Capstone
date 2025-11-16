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
  const [selectedKeyword, setSelectedKeyword] = useState<string>('전체');
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 키워드 옵션 생성 (피드 아이템에서 추출)
  const keywordAvatars: Record<string, string> = useMemo(() => {
    return feedItems.reduce((acc, item) => {
      if (!acc[item.keyword]) {
        acc[item.keyword] = item.imageUri;
      }
      return acc;
    }, {} as Record<string, string>);
  }, [feedItems]);

  const keywordOptions = useMemo(() => ['전체', ...Object.keys(keywordAvatars)], [keywordAvatars]);

  // 키워드 필터링
  const filteredItems = useMemo(() => {
    if (selectedKeyword === '전체') {
      return feedItems;
    }
    return feedItems.filter((item) => item.keyword === selectedKeyword);
  }, [selectedKeyword, feedItems]);

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

  const handleKeywordPress = (keyword: string) => {
    setSelectedKeyword(keyword);
  };

  const handleNavigateKeyword = (keyword: string) => {
    router.push({ pathname: '/keyword/[keyword]', params: { keyword } });
  };

  const renderKeywordHeader = useCallback(
    () => (
      <View style={styles.keywordHeader}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.keywordRow}>
          {keywordOptions.map((keyword) => {
            const isActive = keyword === selectedKeyword;
            const avatarUri = keyword === '전체' ? DEFAULT_AVATAR : keywordAvatars[keyword] ?? DEFAULT_AVATAR;
            return (
              <Pressable
                key={keyword}
                onPress={() => handleKeywordPress(keyword)}
                style={({ pressed }) => [
                  styles.keywordRadio,
                  isActive && styles.keywordRadioActive,
                  pressed && styles.keywordRadioPressed,
                ]}
              >
                <Image source={{ uri: avatarUri }} style={[styles.keywordAvatar, isActive && styles.keywordAvatarActive]} />
                <Text style={[styles.keywordLabel, isActive && styles.keywordLabelActive]} numberOfLines={1}>
                  {keyword}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>
    ),
    [selectedKeyword, keywordOptions, keywordAvatars]
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
        {renderKeywordHeader()}
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
        {renderKeywordHeader()}
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
      {renderKeywordHeader()}
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.id}
        renderSectionHeader={handleRenderSectionHeader}
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
            onPressImage={() => handleNavigateKeyword(item.keyword)}
            onPressKeyword={() => handleNavigateKeyword(item.keyword)}
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
            <Text style={styles.emptyTitle}>해당 키워드의 새 소식이 없어요</Text>
            <Text style={styles.emptyBody}>관심 있는 키워드를 팔로우하면 이곳에서 최신 업데이트를 볼 수 있어요.</Text>
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
  keywordHeader: {
    backgroundColor: '#ffffff',
  },
  sectionWrapper: {
    backgroundColor: '#ffffff',
  },
  keywordRow: {
    paddingHorizontal: 20,
    paddingBottom: 8,
    gap: 16,
  },
  keywordRadio: {
    alignItems: 'center',
    width: 72,
    gap: 6,
    opacity: 0.75,
  },
  keywordRadioActive: {
    opacity: 1,
  },
  keywordRadioPressed: {
    opacity: 0.6,
  },
  keywordAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#e5e7eb',
  },
  keywordAvatarActive: {
    borderWidth: 2,
    borderColor: '#2563eb',
  },
  keywordLabel: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
  },
  keywordLabelActive: {
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
