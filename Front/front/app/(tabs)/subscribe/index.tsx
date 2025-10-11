import { SectionList, StyleSheet, Text, View, Pressable, Image, ScrollView } from 'react-native';
import { useMemo, useState, useCallback } from 'react';
import { useRouter } from 'expo-router';

import { FeedCard } from '@/components/FeedCard';
import feedItemsData from '@/test_data/feedItems.json';

const DEFAULT_AVATAR = 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=160&q=80';

type FeedItem = {
  id: string;
  title: string;
  date: string;
  summary: string;
  content: string;
  imageUri: string;
  keyword: string;
};

type FeedSection = {
  title: string;
  data: FeedItem[];
};

const feedItems = feedItemsData as FeedItem[];

const keywordAvatars: Record<string, string> = feedItems.reduce((acc, item) => {
  if (!acc[item.keyword]) {
    acc[item.keyword] = item.imageUri;
  }
  return acc;
}, {} as Record<string, string>);

const keywordOptions = ['전체', ...Object.keys(keywordAvatars)];

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
  const [selectedKeyword, setSelectedKeyword] = useState<string>('전체');
  const filteredItems = useMemo(() => {
    if (selectedKeyword === '전체') {
      return feedItems;
    }
    return feedItems.filter((item) => item.keyword === selectedKeyword);
  }, [selectedKeyword]);

  const sections = useMemo(() => groupFeedByDate(filteredItems), [filteredItems]);

  const handleKeywordPress = (keyword: string) => {
    setSelectedKeyword(keyword);
  };

  const handleNavigateKeyword = (keyword: string) => {
    router.push({ pathname: '/keyword/[keyword]', params: { keyword } });
  };

  const renderKeywordHeader = useCallback(() => (
    <View style={styles.keywordHeader}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.keywordRow}
      >
        {keywordOptions.map((keyword) => {
          const isActive = keyword === selectedKeyword;
          const avatarUri = keyword === '전체' ? DEFAULT_AVATAR : keywordAvatars[keyword] ?? DEFAULT_AVATAR;
          return (
            <Pressable
              key={keyword}
              onPress={() => handleKeywordPress(keyword)}
              style={({ pressed }) => [styles.keywordRadio, isActive && styles.keywordRadioActive, pressed && styles.keywordRadioPressed]}
            >
              <Image
                source={{ uri: avatarUri }}
                style={[styles.keywordAvatar, isActive && styles.keywordAvatarActive]}
              />
              <Text style={[styles.keywordLabel, isActive && styles.keywordLabelActive]} numberOfLines={1}>
                {keyword}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  ), [selectedKeyword]);

  const handleRenderSectionHeader = ({ section: { title } }: { section: FeedSection }) => (
    <View style={styles.sectionWrapper}>
      <View style={styles.sectionHeader}>
        <View style={styles.sectionDivider} />
        <Text style={styles.sectionHeaderText}>{title}</Text>
        <View style={styles.sectionDivider} />
      </View>
    </View>
  );

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
});
