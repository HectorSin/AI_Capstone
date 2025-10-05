import { memo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

type ArticleDetailProps = {
  title: string;
  keyword: string;
  summary?: string;
  content: string;
  date?: string;
};

function ArticleDetailComponent({ title, keyword, summary, content, date }: ArticleDetailProps) {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.metaSection}>
        <Text style={styles.keyword}>{keyword}</Text>
        <Text style={styles.title}>{title}</Text>
        {summary ? <Text style={styles.summary}>{summary}</Text> : null}
        {date ? <Text style={styles.date}>{date}</Text> : null}
      </View>
      <Text style={styles.body}>{content}</Text>
    </ScrollView>
  );
}

export const ArticleDetail = memo(ArticleDetailComponent);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  contentContainer: {
    paddingBottom: 48,
  },
  metaSection: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 16,
    gap: 8,
  },
  keyword: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6366f1',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    lineHeight: 32,
  },
  summary: {
    fontSize: 15,
    lineHeight: 22,
    color: '#4b5563',
  },
  date: {
    fontSize: 13,
    color: '#6b7280',
  },
  body: {
    paddingHorizontal: 20,
    fontSize: 16,
    lineHeight: 26,
    color: '#1f2937',
  },
});
