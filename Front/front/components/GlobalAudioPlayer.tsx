import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAudioPlayer } from '@/providers/AudioPlayerProvider';
import { formatDuration } from '@/utils/format';

export function GlobalAudioPlayer() {
  const insets = useSafeAreaInsets();
  const {
    playbackState,
    currentPlaylist,
    currentSegmentIndex,
    isLoadingSound,
    togglePlay,
    seekTo,
    seekBy,
    nextSegment,
    previousSegment,
    closePlayer,
  } = useAudioPlayer();

  // 플레이어가 활성화되지 않았으면 아무것도 표시하지 않음
  if (!currentPlaylist) {
    return null;
  }

  const currentSegment = currentPlaylist.segments[currentSegmentIndex];
  const totalSegments = currentPlaylist.segments.length;

  // 탭 바 높이 계산 (보통 49px + safe area bottom)
  const tabBarHeight = 49 + insets.bottom;

  return (
    <View style={[styles.playerContainer, { bottom: tabBarHeight }]}>
      <View style={styles.playerHeader}>
        <View style={styles.headerInfo}>
          <Text style={styles.playerTitle} numberOfLines={1}>
            {currentSegment.title}
          </Text>
          <Text style={styles.playerSubtitle}>
            {currentPlaylist.date} · {currentSegment.topicName}
          </Text>
        </View>
        <Pressable onPress={closePlayer} style={styles.closeButton}>
          <Ionicons name="close" size={20} color="#6b7280" />
        </Pressable>
      </View>

      <Slider
        style={styles.slider}
        minimumValue={0}
        maximumValue={playbackState.durationMillis || 1}
        value={playbackState.positionMillis}
        onSlidingComplete={(value) => seekTo(value)}
        minimumTrackTintColor="#2563eb"
        maximumTrackTintColor="#e5e7eb"
        thumbTintColor="#2563eb"
        disabled={!playbackState.isLoaded || isLoadingSound}
      />

      <View style={styles.timeRow}>
        <Text style={styles.timeLabel}>
          {formatDuration(playbackState.positionMillis / 1000)}
        </Text>
        <Text style={styles.segmentCounter}>
          {currentSegmentIndex + 1} / {totalSegments}
        </Text>
        <Text style={styles.timeLabel}>
          {formatDuration((playbackState.durationMillis || 0) / 1000)}
        </Text>
      </View>

      <View style={styles.controlsRow}>
        <Pressable
          onPress={previousSegment}
          disabled={currentSegmentIndex === 0 || isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            (currentSegmentIndex === 0 || isLoadingSound) && styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed,
          ]}
        >
          <Ionicons
            name="play-skip-back"
            size={24}
            color={currentSegmentIndex === 0 || isLoadingSound ? '#9ca3af' : '#374151'}
          />
        </Pressable>

        <Pressable
          onPress={() => seekBy(-10)}
          disabled={isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            isLoadingSound && styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed,
          ]}
        >
          <Ionicons name="play-back" size={24} color={isLoadingSound ? '#9ca3af' : '#374151'} />
          <Text style={styles.seekLabel}>10</Text>
        </Pressable>

        <Pressable
          onPress={togglePlay}
          disabled={!playbackState.isLoaded || isLoadingSound}
          style={({ pressed }) => [
            styles.playButton,
            (!playbackState.isLoaded || isLoadingSound) && styles.playButtonDisabled,
            pressed && styles.playButtonPressed,
          ]}
        >
          <Ionicons
            name={playbackState.isPlaying ? 'pause' : 'play'}
            size={32}
            color="#ffffff"
            style={playbackState.isPlaying ? {} : { marginLeft: 3 }}
          />
        </Pressable>

        <Pressable
          onPress={() => seekBy(10)}
          disabled={isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            isLoadingSound && styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed,
          ]}
        >
          <Ionicons name="play-forward" size={24} color={isLoadingSound ? '#9ca3af' : '#374151'} />
          <Text style={styles.seekLabel}>10</Text>
        </Pressable>

        <Pressable
          onPress={nextSegment}
          disabled={currentSegmentIndex + 1 >= totalSegments || isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            (currentSegmentIndex + 1 >= totalSegments || isLoadingSound) &&
              styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed,
          ]}
        >
          <Ionicons
            name="play-skip-forward"
            size={24}
            color={
              currentSegmentIndex + 1 >= totalSegments || isLoadingSound ? '#9ca3af' : '#374151'
            }
          />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  playerContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingVertical: 24,
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowOffset: { width: 0, height: -4 },
    shadowRadius: 12,
    elevation: 12,
  },
  playerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  headerInfo: {
    flex: 1,
    marginRight: 12,
  },
  playerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
    lineHeight: 24,
  },
  playerSubtitle: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 4,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  slider: {
    width: '100%',
    height: 40,
    marginVertical: 8,
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  timeLabel: {
    fontSize: 12,
    color: '#6b7280',
    fontWeight: '500',
  },
  segmentCounter: {
    fontSize: 11,
    color: '#9ca3af',
    fontWeight: '600',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  controlButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlButtonPressed: {
    opacity: 0.6,
    backgroundColor: '#e5e7eb',
  },
  controlButtonDisabled: {
    opacity: 0.3,
  },
  seekLabel: {
    fontSize: 9,
    color: '#6b7280',
    fontWeight: '600',
    position: 'absolute',
    bottom: 6,
  },
  playButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#2563eb',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#2563eb',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 8,
    elevation: 6,
  },
  playButtonPressed: {
    opacity: 0.85,
    transform: [{ scale: 0.95 }],
  },
  playButtonDisabled: {
    opacity: 0.5,
    backgroundColor: '#94a3b8',
  },
});
