import { useMemo, useState, useEffect, useCallback } from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';
import {
  FlatList,
  Image,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';

import { FeedCard } from '@/components/FeedCard';
import { getArticlesByKeyword } from '@/utils/api';
import type { FeedItem } from '@/types';

const DEFAULT_AVATAR = 'https://images.unsplash.com/photo-500648767791-00dcc994a43e?auto=format&fit=crop&w=160&q=80';

export default function KeywordScreen() {
  const { keyword } = useLocalSearchParams<{ keyword?: string }>();
  const router = useRouter();
  const [isFollowing, setIsFollowing] = useState(false);
  const [keywordItems, setKeywordItems] = useState<FeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const keywordText = typeof keyword === 'string' ? keyword : 'Unknown';

  const leadItem = keywordItems[0];
  const avatarSource = { uri: leadItem?.imageUri ?? DEFAULT_AVATAR };

  const loadArticles = useCallback(async (isRefresh = false) => {
    if (!keywordText) {
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
      const response = await getArticlesByKeyword(keywordText, 0, 50);
      setKeywordItems(response.items);
    } catch (err) {
      console.error('[Keyword] Failed to load articles:', err);
      setError(err instanceof Error ? err.message : 'Article을 불러올 수 없습니다');
      setKeywordItems([]);
    } finally {
      if (isRefresh) {
        setIsRefreshing(false);
      } else {
        setIsLoading(false);
      }
    }
  }, [keywordText]);

  const handleRefresh = useCallback(() => {
    loadArticles(true);
  }, [loadArticles]);

  useEffect(() => {
    loadArticles();
  }, [loadArticles]);

  const handleFollowToggle = () => {
    setIsFollowing((prev) => !prev);
  };

  const renderItem = ({ item }: { item: FeedItem }) => (
    <FeedCard
      title={item.title}
      summary={item.summary}
      imageUri={item.imageUri}
      keyword={item.keyword}
      date={item.date}
      showDate
      onPressCard={() => router.push({ pathname: '/article/[id]', params: { id: item.id } })}
      onPressImage={() => router.push({ pathname: '/keyword/[keyword]', params: { keyword: item.keyword } })}
      onPressKeyword={() => router.push({ pathname: '/keyword/[keyword]', params: { keyword: item.keyword } })}
    />
  );

  const renderHeader = () => (
    <View style={styles.heroContainer}>
      <Image source={avatarSource} style={styles.avatar} />
      <Text style={styles.keywordText}>{keywordText}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.badgeRow}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>AI</Text>
        </View>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Trend</Text>
        </View>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Insights</Text>
        </View>
      </ScrollView>
      <Pressable
        onPress={handleFollowToggle}
        style={({ pressed }) => [styles.followButton, pressed && styles.followButtonPressed]}
      >
        <Text style={styles.followText}>{isFollowing ? 'Following' : 'Follow'}</Text>
      </Pressable>
    </View>
  );

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.headerBar}>
        <Pressable
          onPress={() => router.back()}
          hitSlop={8}
          style={({ pressed }) => [styles.backButton, pressed && styles.buttonPressed]}
        >
          <Text style={styles.backText}>뒤로</Text>
        </Pressable>
      </View>
      <FlatList
        data={keywordItems}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        ListHeaderComponent={
          isLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#2563eb" />
              <Text style={styles.loadingText}>Article을 불러오는 중...</Text>
            </View>
          ) : error ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorTitle}>Article을 불러올 수 없습니다</Text>
              <Text style={styles.errorMessage}>{error}</Text>
              <Text style={styles.errorHint} onPress={() => loadArticles()}>
                다시 시도
              </Text>
            </View>
          ) : (
            renderHeader()
          )
        }
        ListEmptyComponent={
          !isLoading && !error ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyTitle}>아직 콘텐츠가 없어요</Text>
              <Text style={styles.emptyBody}>곧 {keywordText} 관련 새로운 업데이트가 올라올 예정이에요.</Text>
            </View>
          ) : null
        }
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
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  headerBar: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 4,
  },
  backButton: {
    alignSelf: 'flex-start',
  },
  buttonPressed: {
    opacity: 0.5,
  },
  backText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  heroContainer: {
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#e5e7eb',
  },
  keywordText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 4,
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: '#f3f4f6',
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4b5563',
  },
  followButton: {
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: '#111827',
  },
  followButtonPressed: {
    opacity: 0.8,
  },
  followText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  listContent: {
    paddingBottom: 32,
  },
  emptyState: {
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 24,
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  emptyBody: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  loadingContainer: {
    alignItems: 'center',
    gap: 12,
    paddingVertical: 64,
  },
  loadingText: {
    fontSize: 14,
    color: '#6b7280',
  },
  errorContainer: {
    alignItems: 'center',
    gap: 12,
    paddingVertical: 64,
    paddingHorizontal: 32,
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
