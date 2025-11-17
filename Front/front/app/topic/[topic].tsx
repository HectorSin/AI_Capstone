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
  Alert,
} from 'react-native';

import { FeedCard } from '@/components/FeedCard';
import { getArticlesByTopic, getTopicByName } from '@/utils/api';
import { useAuth } from '@/providers/AuthProvider';
import type { FeedItem, Topic } from '@/types';

const DEFAULT_AVATAR = 'https://images.unsplash.com/photo-500648767791-00dcc994a43e?auto=format&fit=crop&w=160&q=80';

export default function TopicScreen() {
  const { topic } = useLocalSearchParams<{ topic?: string }>();
  const router = useRouter();
  const { subscribeTopic, unsubscribeTopic, isTopicSubscribed, token } = useAuth();
  const [topicInfo, setTopicInfo] = useState<Topic | null>(null);
  const [topicItems, setTopicItems] = useState<FeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const topicName = typeof topic === 'string' ? topic : 'Unknown';

  // 현재 토픽의 ID (Topic API에서 가져온 정보 사용)
  const currentTopicId = topicInfo?.id;

  const isSubscribed = useMemo(() => {
    if (!currentTopicId) return false;
    return isTopicSubscribed(currentTopicId);
  }, [currentTopicId, isTopicSubscribed]);

  const avatarSource = { uri: topicInfo?.image_uri ?? DEFAULT_AVATAR };

  const loadTopicInfo = useCallback(async () => {
    if (!topicName) return;

    try {
      const info = await getTopicByName(topicName);
      setTopicInfo(info);
    } catch (err) {
      console.error('[Topic] Failed to load topic info:', err);
      setError(err instanceof Error ? err.message : 'Topic 정보를 불러올 수 없습니다');
    }
  }, [topicName]);

  const loadArticles = useCallback(async (isRefresh = false) => {
    if (!topicName) {
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
      const response = await getArticlesByTopic(topicName, 0, 50);
      setTopicItems(response.items);
    } catch (err) {
      console.error('[Topic] Failed to load articles:', err);
      setError(err instanceof Error ? err.message : 'Article을 불러올 수 없습니다');
      setTopicItems([]);
    } finally {
      if (isRefresh) {
        setIsRefreshing(false);
      } else {
        setIsLoading(false);
      }
    }
  }, [topicName]);

  const handleRefresh = useCallback(() => {
    loadArticles(true);
  }, [loadArticles]);

  useEffect(() => {
    loadTopicInfo();
    loadArticles();
  }, [loadTopicInfo, loadArticles]);

  const handleSubscribeToggle = async () => {
    if (!token) {
      Alert.alert('알림', '로그인이 필요합니다.');
      return;
    }

    if (!currentTopicId) {
      Alert.alert('알림', '토픽 정보를 불러올 수 없습니다.');
      return;
    }

    setIsSubscribing(true);
    try {
      let success = false;
      if (isSubscribed) {
        success = await unsubscribeTopic(currentTopicId);
        if (success) {
          Alert.alert('구독 취소', `${topicName} 토픽 구독이 취소되었습니다.`);
        }
      } else {
        success = await subscribeTopic(currentTopicId);
        if (success) {
          Alert.alert('구독 완료', `${topicName} 토픽을 구독했습니다!`);
        }
      }

      if (!success) {
        Alert.alert('오류', '구독 상태를 변경할 수 없습니다. 다시 시도해주세요.');
      }
    } catch (error) {
      console.error('[Topic] Subscribe toggle failed:', error);
      Alert.alert('오류', '구독 상태를 변경하는 중 오류가 발생했습니다.');
    } finally {
      setIsSubscribing(false);
    }
  };

  const renderItem = ({ item }: { item: FeedItem }) => (
    <FeedCard
      title={item.title}
      summary={item.summary}
      imageUri={item.imageUri}
      topic={item.topic}
      date={item.date}
      showDate
      onPressCard={() => router.push({ pathname: '/article/[id]', params: { id: item.id } })}
      onPressImage={() => router.push({ pathname: '/topic/[topic]', params: { topic: item.topic } })}
      onPressTopic={() => router.push({ pathname: '/topic/[topic]', params: { topic: item.topic } })}
    />
  );

  const renderHeader = () => (
    <View style={styles.heroContainer}>
      <Image source={avatarSource} style={styles.avatar} />
      <Text style={styles.topicText}>{topicName}</Text>
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
        onPress={handleSubscribeToggle}
        disabled={isSubscribing}
        style={({ pressed }) => [
          styles.subscribeButton,
          isSubscribed && styles.subscribeButtonActive,
          pressed && styles.subscribeButtonPressed,
          isSubscribing && styles.subscribeButtonDisabled,
        ]}
      >
        <Text style={[styles.subscribeText, isSubscribed && styles.subscribeTextActive]}>
          {isSubscribing ? '처리 중...' : isSubscribed ? '구독 중' : '구독하기'}
        </Text>
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
        data={topicItems}
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
              <Text style={styles.emptyBody}>곧 {topicName} 관련 새로운 업데이트가 올라올 예정이에요.</Text>
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
  topicText: {
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
  subscribeButton: {
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: '#2563eb',
    borderWidth: 2,
    borderColor: '#2563eb',
  },
  subscribeButtonActive: {
    backgroundColor: '#ffffff',
  },
  subscribeButtonPressed: {
    opacity: 0.8,
  },
  subscribeButtonDisabled: {
    opacity: 0.6,
  },
  subscribeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  subscribeTextActive: {
    color: '#2563eb',
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
