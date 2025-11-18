import { memo } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';

type ArticleDetailProps = {
  title: string;
  topic: string;
  imageUri?: string;
  summary?: string;
  content: string;
  date?: string;
  onPressTopic?: () => void;
};

function ArticleDetailComponent({ title, topic, imageUri, summary, content, date, onPressTopic }: ArticleDetailProps) {
  const avatarSource = imageUri ?? 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=160&q=80';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.metaSection}>
        <View style={styles.topicRow}>
          <Pressable
            onPress={onPressTopic}
            hitSlop={6}
            style={({ pressed }) => [styles.topicAvatarWrapper, pressed && styles.topicPressed]}
          >
            <Image source={{ uri: avatarSource }} style={styles.topicAvatar} />
          </Pressable>
          <Pressable
            onPress={onPressTopic}
            hitSlop={6}
            style={({ pressed }) => [styles.topicTextWrapper, pressed && styles.topicPressed]}
          >
            <Text style={styles.topicText}>{topic}</Text>
          </Pressable>
        </View>
        <Text style={styles.title}>{title}</Text>
        {summary ? <Text style={styles.summary}>{summary}</Text> : null}
        {date ? <Text style={styles.date}>{date}</Text> : null}
      </View>
      <View style={styles.bodyContainer}>
        <Markdown style={markdownStyles}>{content}</Markdown>
      </View>
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
  topicRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  topicAvatarWrapper: {
    width: 32,
    height: 32,
    borderRadius: 16,
    overflow: 'hidden',
  },
  topicAvatar: {
    width: '100%',
    height: '100%',
    backgroundColor: '#e5e7eb',
  },
  topicText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4338ca',
  },
  topicTextWrapper: {
    paddingHorizontal: 4,
  },
  topicPressed: {
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
  bodyContainer: {
    paddingHorizontal: 20,
  },
});

// 마크다운 스타일 정의
const markdownStyles = StyleSheet.create({
  body: {
    fontSize: 16,
    lineHeight: 26,
    color: '#1f2937',
  },
  paragraph: {
    marginBottom: 12,
    fontSize: 16,
    lineHeight: 26,
    color: '#1f2937',
  },
  strong: {
    fontWeight: '700',
    color: '#111827',
  },
  em: {
    fontStyle: 'italic',
  },
  heading1: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginTop: 24,
    marginBottom: 12,
    lineHeight: 32,
  },
  heading2: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginTop: 20,
    marginBottom: 10,
    lineHeight: 28,
  },
  heading3: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
    lineHeight: 24,
  },
  bullet_list: {
    marginBottom: 12,
  },
  ordered_list: {
    marginBottom: 12,
  },
  list_item: {
    marginBottom: 6,
    fontSize: 16,
    lineHeight: 26,
    color: '#1f2937',
  },
  code_inline: {
    backgroundColor: '#f3f4f6',
    color: '#dc2626',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontSize: 15,
    fontFamily: 'Courier',
  },
  code_block: {
    backgroundColor: '#f3f4f6',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    fontSize: 14,
    lineHeight: 20,
    fontFamily: 'Courier',
  },
  fence: {
    backgroundColor: '#f3f4f6',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    fontSize: 14,
    lineHeight: 20,
    fontFamily: 'Courier',
  },
  blockquote: {
    backgroundColor: '#f9fafb',
    borderLeftWidth: 4,
    borderLeftColor: '#2563eb',
    paddingLeft: 12,
    paddingVertical: 8,
    marginBottom: 12,
  },
  link: {
    color: '#2563eb',
    textDecorationLine: 'underline',
  },
  hr: {
    backgroundColor: '#e5e7eb',
    height: 1,
    marginVertical: 16,
  },
});
