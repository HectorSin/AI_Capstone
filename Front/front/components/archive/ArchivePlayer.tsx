import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Audio, AVPlaybackStatus, InterruptionModeAndroid, InterruptionModeIOS } from 'expo-av';

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

  const progressLabel = useMemo(() => {
    const played = formatDuration(playbackState.positionMillis / 1000);
    const total = formatDuration((playbackState.durationMillis || 0) / 1000);
    return `${played} / ${total}`;
  }, [playbackState.durationMillis, playbackState.positionMillis]);

  return (
    <View style={styles.playerContainer}>
      <View style={styles.playerHeader}>
        <Text style={styles.playerTitle}>{playlist.date} · {currentSegment.topicName}</Text>
        <Pressable onPress={() => { onClose(); }}>
          <Text style={styles.closeLabel}>닫기</Text>
        </Pressable>
      </View>
      <Text style={styles.segmentTitle}>{currentSegment.title}</Text>
      <View style={styles.progressBar}>
        <View style={[styles.progressBarFill, { width: `${Math.min(progress * 100, 100)}%` }]} />
      </View>
      <Text style={styles.progressLabel}>{progressLabel}</Text>
      <View style={styles.controlsRow}>
        <Pressable onPress={handlePrev} disabled={currentIndex === 0 || isLoadingSound} style={[styles.controlButton, currentIndex === 0 && styles.controlDisabled]}>
          <Text style={styles.controlLabel}>이전</Text>
        </Pressable>
        <Pressable onPress={togglePlay} disabled={isLoadingSound} style={styles.playButton}>
          <Text style={styles.playLabel}>{playbackState.isPlaying ? '일시정지' : '재생'}</Text>
        </Pressable>
        <Pressable onPress={handleNext} disabled={currentIndex + 1 >= totalSegments || isLoadingSound} style={[styles.controlButton, currentIndex + 1 >= totalSegments && styles.controlDisabled]}>
          <Text style={styles.controlLabel}>다음</Text>
        </Pressable>
      </View>
      <Text style={styles.segmentCounter}>
        {currentIndex + 1} / {totalSegments}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  playerContainer: {
    paddingHorizontal: 16,
    paddingVertical: 20,
    borderTopColor: '#e5e7eb',
    borderTopWidth: 1,
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: -2 },
    shadowRadius: 8,
    elevation: 10,
  },
  playerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  playerTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  closeLabel: {
    fontSize: 14,
    color: '#dc2626',
  },
  segmentTitle: {
    fontSize: 14,
    color: '#4b5563',
    marginTop: 4,
  },
  progressBar: {
    height: 6,
    borderRadius: 999,
    backgroundColor: '#e5e7eb',
    marginTop: 16,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: 6,
    backgroundColor: '#2563eb',
  },
  progressLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'right',
  },
  controlsRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
    alignItems: 'center',
  },
  controlButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
  },
  controlDisabled: {
    opacity: 0.5,
  },
  controlLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  playButton: {
    flex: 1.4,
    borderRadius: 10,
    paddingVertical: 12,
    backgroundColor: '#2563eb',
    alignItems: 'center',
  },
  playLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ffffff',
  },
  segmentCounter: {
    marginTop: 12,
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
  },
});
