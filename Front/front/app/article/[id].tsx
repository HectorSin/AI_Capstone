import { useCallback, useMemo } from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Share, StyleSheet, SafeAreaView, View } from 'react-native';

import { ArticleDetail } from '@/components/ArticleDetail';
import { NavigationHeader } from '@/components/NavigationHeader';
import feedItemsData from '@/test_data/feedItems.json';
import type { FeedItem } from '@/types';

const feedItems = feedItemsData as FeedItem[];

const FALLBACK_ITEM: FeedItem = {
  id: 'fallback',
  title: '새로운 인사이트를 준비 중이에요',
  date: '알 수 없음',
  summary: '요청한 피드를 찾지 못했어요. 대신 최신 트렌드 요약을 확인해 주세요.',
  content:
    '요청한 피드를 찾지 못했어요. 대신 최근 AI 업계에서 주목받는 이슈와 실제 사례를 정리해 드립니다. 데이터 인프라 구축, 모델 배포 전략, 팀 협업 팁 등 바로 활용할 수 있는 내용으로 구성했어요. 홈 화면으로 돌아가 최신 피드를 확인하거나, 검색 기능을 통해 원하는 항목을 찾아보세요.',
  imageUri: 'https://images.unsplash.com/photo-1523473827534-86c4e00c07a3?auto=format&fit=crop&w=640&q=80',
  keyword: 'AI INSIGHT',
};

export default function ArticleScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const router = useRouter();

  const feedItem = useMemo(() => feedItems.find((item) => item.id === id) ?? FALLBACK_ITEM, [id]);

  const handleShare = useCallback(async () => {
    try {
      const shareMessage = `${feedItem.title}\n\n${feedItem.summary || ''}\n\n${feedItem.content}`.trim();
      await Share.share({
        title: feedItem.title,
        message: shareMessage,
      });
    } catch (error) {
      console.warn('Share failed', error);
    }
  }, [feedItem]);

  return (
    <SafeAreaView style={styles.screen}>
      <NavigationHeader
        onBack={() => router.back()}
        rightButton={{
          text: '공유',
          onPress: handleShare,
          variant: 'secondary',
        }}
      />
      <View style={styles.content}>
        <ArticleDetail
          title={feedItem.title}
          keyword={feedItem.keyword}
          imageUri={feedItem.imageUri}
          summary={feedItem.summary}
          content={feedItem.content}
          date={feedItem.date}
          onPressKeyword={() =>
            router.push({
              pathname: '/keyword/[keyword]',
              params: { keyword: feedItem.keyword },
            })
          }
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  content: {
    flex: 1,
  },
});
