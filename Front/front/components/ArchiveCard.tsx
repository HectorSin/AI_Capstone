import { memo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

const formatDuration = (seconds: number) => {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return '';
  }

  const totalSeconds = Math.floor(seconds);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;

  const paddedMinutes = hours > 0 ? minutes.toString().padStart(2, '0') : minutes.toString();
  const paddedSeconds = secs.toString().padStart(2, '0');

  return hours > 0 ? `${hours}:${paddedMinutes}:${paddedSeconds}` : `${minutes}:${paddedSeconds}`;
};

type ArchiveCardProps = {
  date: string;
  keywords: string[];
  onPressCard?: () => void;
  onPressDownload?: () => void;
  onPressPlay?: () => void;
  durationSeconds?: number;
};

function ArchiveCardComponent({
  date,
  keywords,
  onPressCard,
  onPressDownload,
  onPressPlay,
  durationSeconds,
}: ArchiveCardProps) {
  const title = `${date} 팟캐스트`;
  const formattedDuration = durationSeconds !== undefined ? formatDuration(durationSeconds) : undefined;
  const durationLabel = formattedDuration || undefined;

  return (
    <Pressable onPress={onPressCard} style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}>
      <View style={styles.bottomSection}>
        <View style={styles.headerRow}>
          <Text style={styles.title}>{title}</Text>
          {durationLabel ? <Text style={styles.duration}>{durationLabel}</Text> : null}
        </View>
        <View style={styles.keywordsContainer}>
          {keywords.map((keyword, index) => (
            <View key={`${keyword}-${index}`} style={styles.keywordBadge}>
              <Text style={styles.keywordText}>{keyword}</Text>
            </View>
          ))}
        </View>
        <View style={styles.buttonRow}>
          <Pressable onPress={onPressDownload} style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}>
            <Text style={styles.buttonText}>다운로드</Text>
          </Pressable>
          <Pressable onPress={onPressPlay} style={({ pressed }) => [styles.button, styles.playButton, pressed && styles.buttonPressed]}>
            <Text style={[styles.buttonText, styles.playButtonText]}>재생</Text>
          </Pressable>
        </View>
      </View>
    </Pressable>
  );
}

export const ArchiveCard = memo(ArchiveCardComponent);

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
  bottomSection: {
    gap: 10,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  duration: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  keywordBadge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
    backgroundColor: '#e5e7eb',
  },
  keywordText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#374151',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#e5e7eb',
  },
  playButton: {
    backgroundColor: '#111827',
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },
  playButtonText: {
    color: '#ffffff',
  },
});
