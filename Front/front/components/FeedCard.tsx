import { memo } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';

type FeedCardProps = {
  imageUri: string;
  title: string;
  content: string;
  keyword: string;
};

function FeedCardComponent({ imageUri, title, content, keyword }: FeedCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.topSection}>
        <Image source={{ uri: imageUri }} style={styles.avatar} />
        <Text style={styles.keywordText}>{keyword}</Text>
      </View>
      <View style={styles.bottomSection}>
        <Text style={styles.title}>{title}</Text>
        <Text numberOfLines={3} style={styles.content}>
          {content}
        </Text>
      </View>
    </View>
  );
}

export const FeedCard = memo(FeedCardComponent);

const styles = StyleSheet.create({
  card: {
    paddingVertical: 24,
    gap: 10,
  },
  topSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#e5e7eb',
  },
  keywordText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  bottomSection: {
    gap: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  content: {
    fontSize: 15,
    lineHeight: 22,
    color: '#374151',
  },
});
