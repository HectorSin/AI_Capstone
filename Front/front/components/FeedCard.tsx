import { memo, useState } from 'react';
import type { GestureResponderEvent } from 'react-native';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

type FeedCardProps = {
  imageUri: string;
  title: string;
  summary: string;
  keyword: string;
  onPressCard?: () => void;
  onPressImage?: () => void;
  onPressKeyword?: () => void;
};

function FeedCardComponent({
  imageUri,
  title,
  summary,
  keyword,
  onPressCard,
  onPressImage,
  onPressKeyword,
}: FeedCardProps) {
  const [isTopPressed, setIsTopPressed] = useState(false);

  const handleTopPressIn = (event: GestureResponderEvent) => {
    event.stopPropagation();
    setIsTopPressed(true);
  };

  const handleTopPressOut = (event: GestureResponderEvent) => {
    event.stopPropagation();
    setIsTopPressed(false);
  };

  const handleImagePress = (event: GestureResponderEvent) => {
    event.stopPropagation();
    setIsTopPressed(false);
    onPressImage?.();
  };

  const handleKeywordPress = (event: GestureResponderEvent) => {
    event.stopPropagation();
    setIsTopPressed(false);
    onPressKeyword?.();
  };

  return (
    <Pressable onPress={onPressCard} style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}>
      <View style={styles.topSection}>
        <Pressable
          android_ripple={{ color: '#d1d5db', borderless: false }}
          onPressIn={handleTopPressIn}
          onPressOut={handleTopPressOut}
          onPress={handleImagePress}
          style={styles.avatarPressable}
        >
          {({ pressed }) => (
            <Image
              source={{ uri: imageUri }}
              style={[styles.avatar, (pressed || isTopPressed) && styles.avatarPressed]}
            />
          )}
        </Pressable>
        <Pressable
          android_ripple={{ color: '#d1d5db', borderless: false }}
          onPressIn={handleTopPressIn}
          onPressOut={handleTopPressOut}
          onPress={handleKeywordPress}
          style={styles.keywordPressable}
        >
          {({ pressed }) => {
            const active = pressed || isTopPressed;
            return <Text style={[styles.keywordText, active && styles.keywordTextPressed]}>{keyword}</Text>;
          }}
        </Pressable>
      </View>
      <View style={styles.bottomSection}>
        <Text style={styles.title}>{title}</Text>
        <Text numberOfLines={3} style={styles.summary}>
          {summary}
        </Text>
      </View>
    </Pressable>
  );
}

export const FeedCard = memo(FeedCardComponent);

const styles = StyleSheet.create({
  card: {
    paddingVertical: 20,
    paddingHorizontal: 20,
    gap: 18,
    marginBottom: 16,
    backgroundColor: '#ffffff',
  },
  cardPressed: {
    backgroundColor: '#f3f4f6',
  },
  topSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarPressable: {
    width: 32,
    height: 32,
    borderRadius: 16,
    overflow: 'hidden',
  },
  avatar: {
    width: '100%',
    height: '100%',
  },
  avatarPressed: {
    opacity: 0.7,
  },
  keywordPressable: {
    flex: 1,
    paddingVertical: 4,
  },
  keywordText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  keywordTextPressed: {
    color: '#111827',
  },
  bottomSection: {
    gap: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  summary: {
    fontSize: 15,
    lineHeight: 22,
    color: '#374151',
  },
});
