import { memo } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type ArticleDetailProps = {
  title: string;
  keyword: string;
  imageUri?: string;
  summary?: string;
  content: string;
  date?: string;
  onPressKeyword?: () => void;
};

function ArticleDetailComponent({ title, keyword, imageUri, summary, content, date, onPressKeyword }: ArticleDetailProps) {
  const avatarSource = imageUri ?? 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=160&q=80';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.metaSection}>
        <View style={styles.keywordRow}>
          <Pressable
            onPress={onPressKeyword}
            hitSlop={6}
            style={({ pressed }) => [styles.keywordAvatarWrapper, pressed && styles.keywordPressed]}
          >
            <Image source={{ uri: avatarSource }} style={styles.keywordAvatar} />
          </Pressable>
          <Pressable
            onPress={onPressKeyword}
            hitSlop={6}
            style={({ pressed }) => [styles.keywordTextWrapper, pressed && styles.keywordPressed]}
          >
            <Text style={styles.keywordText}>{keyword}</Text>
          </Pressable>
        </View>
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
  keywordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  keywordAvatarWrapper: {
    width: 32,
    height: 32,
    borderRadius: 16,
    overflow: 'hidden',
  },
  keywordAvatar: {
    width: '100%',
    height: '100%',
    backgroundColor: '#e5e7eb',
  },
  keywordText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4338ca',
  },
  keywordTextWrapper: {
    paddingHorizontal: 4,
  },
  keywordPressed: {
    opacity: 0.7,
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
