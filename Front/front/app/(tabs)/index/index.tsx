import { SectionList, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { FeedCard } from '@/components/FeedCard';
import feedItemsData from '@/test_data/feedItems.json';

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

const feedSections: FeedSection[] = feedItems.reduce<FeedSection[]>((sections, item) => {
  const lastSection = sections[sections.length - 1];
  if (!lastSection || lastSection.title !== item.date) {
    sections.push({ title: item.date, data: [item] });
  } else {
    lastSection.data.push(item);
  }
  return sections;
}, []);

export default function HomeScreen() {
  const router = useRouter();

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
            keyword={item.keyword}
            onPressCard={() =>
              router.push({
                pathname: '[id]',
                params: { id: item.id },
              })
            }
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
    paddingVertical: 4,
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
});
