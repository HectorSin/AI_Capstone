import { memo } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';

type FeedCardProps = {
  imageUri: string;
  title: string;
  content: string;
};

function FeedCardComponent({ imageUri, title, content }: FeedCardProps) {
  return (
    <View style={styles.card}>
      <Image source={{ uri: imageUri }} style={styles.avatar} />
      <View style={styles.body}>
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
    flexDirection: 'row',
    paddingVertical: 16,
    gap: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    marginVertical: 4,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#e5e7eb',
  },
  body: {
    flex: 1,
    gap: 8,
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
