import { SafeAreaView, FlatList, StyleSheet, Text, View } from 'react-native';

import { ArchiveCard } from '@/components/ArchiveCard';
import archiveItemsData from '@/test_data/archiveItems.json';

type ArchiveItem = {
  date: string;
  keywords: string[];
  durationSeconds: number;
};

const archiveItems = archiveItemsData as ArchiveItem[];

export default function ArchiveScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={archiveItems}
        keyExtractor={(item) => item.date}
        renderItem={({ item }) => (
          <ArchiveCard
            date={item.date}
            keywords={item.keywords}
            durationSeconds={item.durationSeconds}
          />
        )}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>보관된 피드가 없어요</Text>
            <Text style={styles.emptyBody}>흥미로운 소식을 보관하면 여기에서 다시 확인할 수 있어요.</Text>
          </View>
        }
      />
    </SafeAreaView>
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
