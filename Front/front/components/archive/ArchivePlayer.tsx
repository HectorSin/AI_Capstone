import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Audio, AVPlaybackStatus, InterruptionModeAndroid, InterruptionModeIOS } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';

import type { DownloadedPlaylist } from '@/utils/archiveStorage';
import { formatDuration } from '@/utils/format';

type ArchivePlayerProps = {
  playlist: DownloadedPlaylist;
  onClose: () => void;
};

type PlaybackState = {
  isLoaded: boolean;
  isPlaying: boolean;
  positionMillis: number;
  durationMillis: number;
};

const initialPlaybackState: PlaybackState = {
  isLoaded: false,
  isPlaying: false,
  positionMillis: 0,
  durationMillis: 0,
};

export function ArchivePlayer({ playlist, onClose }: ArchivePlayerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playbackState, setPlaybackState] = useState<PlaybackState>(initialPlaybackState);
  const soundRef = useRef<any>(null);
  const [isLoadingSound, setIsLoadingSound] = useState(false);
  const [isSeeking, setIsSeeking] = useState(false);
  const [pendingSeek, setPendingSeek] = useState(0);
  const [sliderWidth, setSliderWidth] = useState(0);

  const currentSegment = playlist.segments[currentIndex];
  const totalSegments = playlist.segments.length;

  const setupAudioMode = useCallback(async () => {
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      interruptionModeIOS: InterruptionModeIOS.DuckOthers,
      playsInSilentModeIOS: true,
      shouldDuckAndroid: true,
      interruptionModeAndroid: InterruptionModeAndroid.DuckOthers,
      playThroughEarpieceAndroid: false,
      staysActiveInBackground: false,
    });
  }, []);

  const unloadSound = useCallback(async () => {
    const current = soundRef.current;
    if (!current) {
      return;
    }
    soundRef.current = null;
    try {
      await current.stopAsync();
    } catch {
      // ignore
    }
    try {
      await current.unloadAsync();
    } catch {
      // ignore
    }
    try {
      current.setOnPlaybackStatusUpdate(null);
    } catch {
      // ignore
    }
  }, []);

  const loadCurrentSegment = useCallback(async () => {
    if (!currentSegment) return;
    setIsLoadingSound(true);
    setPlaybackState(initialPlaybackState);
    try {
      await unloadSound();
      await setupAudioMode();
      const { sound } = await Audio.Sound.createAsync(
        { uri: currentSegment.fileUri },
        { shouldPlay: true }
      );
      soundRef.current = sound;
      sound.setOnPlaybackStatusUpdate((status: AVPlaybackStatus) => {
        if (!status.isLoaded) {
          setPlaybackState(initialPlaybackState);
          return;
        }
        setPlaybackState({
          isLoaded: true,
          isPlaying: status.isPlaying,
          positionMillis: status.positionMillis ?? 0,
          durationMillis: status.durationMillis ?? currentSegment.durationSeconds * 1000,
        });

        if (status.didJustFinish) {
          setCurrentIndex((prev) => (prev + 1 < totalSegments ? prev + 1 : 0));
        }
      });
    } catch (error) {
      console.warn('[ArchivePlayer] failed to load segment', error);
      await unloadSound();
    } finally {
      setIsLoadingSound(false);
    }
  }, [currentSegment, totalSegments, setupAudioMode, unloadSound]);

  useEffect(() => {
    loadCurrentSegment();
    return () => {
      unloadSound();
    };
  }, [loadCurrentSegment, unloadSound]);

  const togglePlay = useCallback(async () => {
    if (!playbackState.isLoaded || !soundRef.current) return;
    if (playbackState.isPlaying) {
      await soundRef.current.pauseAsync();
    } else {
      await soundRef.current.playAsync();
    }
  }, [playbackState.isLoaded, playbackState.isPlaying]);

  const handleNext = useCallback(() => {
    if (isLoadingSound) {
      return;
    }
    setCurrentIndex((prev) => (prev + 1 < totalSegments ? prev + 1 : prev));
  }, [isLoadingSound, totalSegments]);

  const handlePrev = useCallback(() => {
    if (isLoadingSound) {
      return;
    }
    setCurrentIndex((prev) => (prev - 1 >= 0 ? prev - 1 : prev));
  }, [isLoadingSound]);

  const progress = useMemo(() => {
    if (!playbackState.durationMillis || playbackState.durationMillis === 0) return 0;
    return playbackState.positionMillis / playbackState.durationMillis;
  }, [playbackState.durationMillis, playbackState.positionMillis]);
  const sliderValue = isSeeking ? pendingSeek : progress;

  const handleSeekToFraction = useCallback(
    async (fraction: number) => {
      if (!soundRef.current) return;
      const duration =
        playbackState.durationMillis ?? (currentSegment?.durationSeconds ? currentSegment.durationSeconds * 1000 : null);
      if (!duration) return;
      const target = Math.min(Math.max(fraction, 0), 1) * duration;
      try {
        await soundRef.current.setPositionAsync(target);
        setPlaybackState((prev) => ({
          ...prev,
          positionMillis: target,
          durationMillis: duration,
        }));
      } catch (error) {
        console.warn('[ArchivePlayer] seekToFraction error', error);
      }
    },
    [playbackState.durationMillis, currentSegment]
  );

  const handleSeekBy = useCallback(
    async (delta: number) => {
      if (!soundRef.current || isLoadingSound) return;
      try {
        const status = await soundRef.current.getStatusAsync();
        if (!status.isLoaded) return;
        const duration =
          status.durationMillis ??
          playbackState.durationMillis ??
          (currentSegment?.durationSeconds ? currentSegment.durationSeconds * 1000 : 0);
        if (!duration) return;
        const next = Math.min(Math.max((status.positionMillis ?? 0) + delta * 1000, 0), duration);
        await soundRef.current.setPositionAsync(next);
        setPlaybackState((prev) => ({
          ...prev,
          positionMillis: next,
          durationMillis: duration,
        }));
      } catch (error) {
        console.warn('[ArchivePlayer] seekBy error', error);
      }
    },
    [playbackState.durationMillis, currentSegment, isLoadingSound]
  );

  const handleProgressGrant = useCallback(
    (value: number) => {
      if (!sliderWidth) return;
      const fraction = Math.min(Math.max(value / sliderWidth, 0), 1);
      setIsSeeking(true);
      setPendingSeek(fraction);
    },
    [sliderWidth]
  );

  const handleProgressMove = useCallback(
    (value: number) => {
      if (!sliderWidth) return;
      const fraction = Math.min(Math.max(value / sliderWidth, 0), 1);
      setIsSeeking(true);
      setPendingSeek(fraction);
    },
    [sliderWidth]
  );

  const handleProgressRelease = useCallback(
    (value: number) => {
      if (!sliderWidth) {
        setIsSeeking(false);
        return;
      }
      const fraction = Math.min(Math.max(value / sliderWidth, 0), 1);
      setIsSeeking(false);
      handleSeekToFraction(fraction);
    },
    [sliderWidth, handleSeekToFraction]
  );

  const progressLabel = useMemo(() => {
    const played = formatDuration(playbackState.positionMillis / 1000);
    const total = formatDuration((playbackState.durationMillis || 0) / 1000);
    return `${played} / ${total}`;
  }, [playbackState.durationMillis, playbackState.positionMillis]);

  return (
    <View style={styles.playerContainer}>
      <View style={styles.playerHeader}>
        <View style={styles.headerInfo}>
          <Text style={styles.playerTitle}>{currentSegment.title}</Text>
          <Text style={styles.playerSubtitle}>{playlist.date} · {currentSegment.topicName}</Text>
        </View>
        <Pressable onPress={() => { onClose(); }} style={styles.closeButton}>
          <Ionicons name="close" size={20} color="#6b7280" />
        </Pressable>
      </View>

      <View
        style={styles.progressBarWrapper}
        onLayout={(event) => setSliderWidth(event.nativeEvent.layout.width)}
        onStartShouldSetResponder={() => true}
        onResponderGrant={(event) => handleProgressGrant(event.nativeEvent.locationX)}
        onResponderMove={(event) => handleProgressMove(event.nativeEvent.locationX)}
        onResponderRelease={(event) => handleProgressRelease(event.nativeEvent.locationX)}
      >
        <View style={styles.progressBar}>
          <View style={[styles.progressBarFill, { width: `${Math.min(sliderValue * 100, 100)}%` }]} />
          <View style={[styles.progressThumb, { left: `${Math.min(sliderValue * 100, 100)}%` }]} />
        </View>
      </View>

      <View style={styles.timeRow}>
        <Text style={styles.timeLabel}>{formatDuration(playbackState.positionMillis / 1000)}</Text>
        <Text style={styles.segmentCounter}>{currentIndex + 1} / {totalSegments}</Text>
        <Text style={styles.timeLabel}>{formatDuration((playbackState.durationMillis || 0) / 1000)}</Text>
      </View>

      <View style={styles.controlsRow}>
        <Pressable
          onPress={handlePrev}
          disabled={currentIndex === 0 || isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            (currentIndex === 0 || isLoadingSound) && styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed
          ]}
        >
          <Ionicons
            name="play-skip-back"
            size={24}
            color={(currentIndex === 0 || isLoadingSound) ? '#9ca3af' : '#374151'}
          />
        </Pressable>

        <Pressable
          onPress={() => handleSeekBy(-10)}
          disabled={isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            isLoadingSound && styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed
          ]}
        >
          <Ionicons
            name="play-back"
            size={24}
            color={isLoadingSound ? '#9ca3af' : '#374151'}
          />
          <Text style={styles.seekLabel}>10</Text>
        </Pressable>

        <Pressable
          onPress={togglePlay}
          disabled={!playbackState.isLoaded || isLoadingSound}
          style={({ pressed }) => [
            styles.playButton,
            (!playbackState.isLoaded || isLoadingSound) && styles.playButtonDisabled,
            pressed && styles.playButtonPressed
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
          onPress={() => handleSeekBy(10)}
          disabled={isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            isLoadingSound && styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed
          ]}
        >
          <Ionicons
            name="play-forward"
            size={24}
            color={isLoadingSound ? '#9ca3af' : '#374151'}
          />
          <Text style={styles.seekLabel}>10</Text>
        </Pressable>

        <Pressable
          onPress={handleNext}
          disabled={currentIndex + 1 >= totalSegments || isLoadingSound}
          style={({ pressed }) => [
            styles.controlButton,
            (currentIndex + 1 >= totalSegments || isLoadingSound) && styles.controlButtonDisabled,
            pressed && styles.controlButtonPressed
          ]}
        >
          <Ionicons
            name="play-skip-forward"
            size={24}
            color={(currentIndex + 1 >= totalSegments || isLoadingSound) ? '#9ca3af' : '#374151'}
          />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  playerContainer: {
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
  progressBarWrapper: {
    marginBottom: 12,
  },
  progressBar: {
    height: 4,
    borderRadius: 2,
    backgroundColor: '#e5e7eb',
    position: 'relative',
  },
  progressBarFill: {
    height: 4,
    backgroundColor: '#2563eb',
    borderRadius: 2,
  },
  progressThumb: {
    position: 'absolute',
    top: -4,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#2563eb',
    marginLeft: -6,
    shadowColor: '#2563eb',
    shadowOpacity: 0.4,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 3,
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
