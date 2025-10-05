import { memo, useState } from 'react';
import type { GestureResponderEvent } from 'react-native';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

type FeedCardProps = {
  imageUri: string;
  title: string;
  content: string;
  keyword: string;
};

function FeedCardComponent({ imageUri, title, content, keyword }: FeedCardProps) {
  const [isCardPressed, setIsCardPressed] = useState(false);
  const [isTopPressed, setIsTopPressed] = useState(false);

  const handleCardPressIn = () => {
    setIsCardPressed(true);
  };

  const handleCardPressOut = () => {
    setIsCardPressed(false);
  };

  const handleTopPressIn = (event: GestureResponderEvent) => {
    event.stopPropagation();
    setIsTopPressed(true);
    setIsCardPressed(false);
  };

  const handleTopPressOut = (event: GestureResponderEvent) => {
    event.stopPropagation();
    setIsTopPressed(false);
  };

  const handleTopPress = (event: GestureResponderEvent) => {
    event.stopPropagation();
    setIsTopPressed(false);
  };

  return (
    <Pressable
      android_ripple={{ color: '#e5e7eb' }}
      onPressIn={handleCardPressIn}
      onPressOut={handleCardPressOut}
      style={[styles.card, isCardPressed && styles.cardPressed]}
    >
      <View style={styles.topSection}>
        <Pressable
          android_ripple={{ color: '#d1d5db', borderless: false }}
          onPressIn={handleTopPressIn}
          onPressOut={handleTopPressOut}
          onPress={handleTopPress}
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
          onPress={handleTopPress}
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
        <Text numberOfLines={3} style={styles.content}>
          {content}
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
  content: {
    fontSize: 15,
    lineHeight: 22,
    color: '#374151',
  },
});
