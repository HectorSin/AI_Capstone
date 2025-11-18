import { createContext, useContext, useState, useCallback, useRef, useEffect, ReactNode } from 'react';
import { Audio, AVPlaybackStatus, InterruptionModeAndroid, InterruptionModeIOS } from 'expo-av';
import type { DownloadedPlaylist, DownloadedSegment } from '@/utils/archiveStorage';

type PlaybackState = {
  isLoaded: boolean;
  isPlaying: boolean;
  positionMillis: number;
  durationMillis: number;
};

type AudioPlayerContextType = {
  // Playback state
  playbackState: PlaybackState;
  currentPlaylist: DownloadedPlaylist | null;
  currentSegmentIndex: number;
  isLoadingSound: boolean;

  // Actions
  loadPlaylist: (playlist: DownloadedPlaylist, startIndex?: number) => Promise<void>;
  togglePlay: () => Promise<void>;
  seekTo: (positionMillis: number) => Promise<void>;
  seekBy: (deltaSeconds: number) => Promise<void>;
  nextSegment: () => void;
  previousSegment: () => void;
  closePlayer: () => void;
};

const AudioPlayerContext = createContext<AudioPlayerContextType | null>(null);

export function useAudioPlayer() {
  const context = useContext(AudioPlayerContext);
  if (!context) {
    throw new Error('useAudioPlayer must be used within AudioPlayerProvider');
  }
  return context;
}

const initialPlaybackState: PlaybackState = {
  isLoaded: false,
  isPlaying: false,
  positionMillis: 0,
  durationMillis: 0,
};

export function AudioPlayerProvider({ children }: { children: ReactNode }) {
  const [playbackState, setPlaybackState] = useState<PlaybackState>(initialPlaybackState);
  const [currentPlaylist, setCurrentPlaylist] = useState<DownloadedPlaylist | null>(null);
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
  const [isLoadingSound, setIsLoadingSound] = useState(false);

  const soundRef = useRef<any>(null);

  const setupAudioMode = useCallback(async () => {
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      interruptionModeIOS: InterruptionModeIOS.DuckOthers,
      playsInSilentModeIOS: true,
      shouldDuckAndroid: true,
      interruptionModeAndroid: InterruptionModeAndroid.DuckOthers,
      playThroughEarpieceAndroid: false,
      staysActiveInBackground: true, // 백그라운드 재생 활성화
    });
  }, []);

  const unloadSound = useCallback(async () => {
    const current = soundRef.current;
    if (!current) return;

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

  const loadSegment = useCallback(async (segment: DownloadedSegment, totalSegments: number) => {
    setIsLoadingSound(true);
    setPlaybackState(initialPlaybackState);

    try {
      await unloadSound();
      await setupAudioMode();

      const { sound } = await Audio.Sound.createAsync(
        { uri: segment.fileUri },
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
          durationMillis: status.durationMillis ?? segment.durationSeconds * 1000,
        });

        if (status.didJustFinish) {
          setCurrentSegmentIndex((prev) => (prev + 1 < totalSegments ? prev + 1 : prev));
        }
      });
    } catch (error) {
      console.warn('[AudioPlayer] failed to load segment', error);
      await unloadSound();
    } finally {
      setIsLoadingSound(false);
    }
  }, [unloadSound, setupAudioMode]);

  // 세그먼트 인덱스가 변경되면 새 세그먼트 로드
  useEffect(() => {
    if (!currentPlaylist) return;

    const segment = currentPlaylist.segments[currentSegmentIndex];
    if (segment) {
      loadSegment(segment, currentPlaylist.segments.length);
    }
  }, [currentSegmentIndex, currentPlaylist, loadSegment]);

  const loadPlaylist = useCallback(async (playlist: DownloadedPlaylist, startIndex: number = 0) => {
    setCurrentPlaylist(playlist);
    setCurrentSegmentIndex(startIndex);
  }, []);

  const togglePlay = useCallback(async () => {
    if (!playbackState.isLoaded || !soundRef.current) return;

    if (playbackState.isPlaying) {
      await soundRef.current.pauseAsync();
    } else {
      await soundRef.current.playAsync();
    }
  }, [playbackState.isLoaded, playbackState.isPlaying]);

  const seekTo = useCallback(async (positionMillis: number) => {
    if (!soundRef.current || !playbackState.isLoaded) return;

    try {
      await soundRef.current.setPositionAsync(positionMillis);
    } catch (error) {
      console.warn('[AudioPlayer] seek error', error);
    }
  }, [playbackState.isLoaded]);

  const seekBy = useCallback(async (deltaSeconds: number) => {
    if (!soundRef.current || !playbackState.isLoaded) return;

    try {
      const newPosition = Math.min(
        Math.max(playbackState.positionMillis + deltaSeconds * 1000, 0),
        playbackState.durationMillis
      );
      await soundRef.current.setPositionAsync(newPosition);
    } catch (error) {
      console.warn('[AudioPlayer] seekBy error', error);
    }
  }, [playbackState.positionMillis, playbackState.durationMillis, playbackState.isLoaded]);

  const nextSegment = useCallback(() => {
    if (!currentPlaylist || isLoadingSound) return;

    const totalSegments = currentPlaylist.segments.length;
    if (currentSegmentIndex + 1 < totalSegments) {
      setCurrentSegmentIndex((prev) => prev + 1);
    }
  }, [currentPlaylist, currentSegmentIndex, isLoadingSound]);

  const previousSegment = useCallback(() => {
    if (!currentPlaylist || isLoadingSound) return;

    if (currentSegmentIndex > 0) {
      setCurrentSegmentIndex((prev) => prev - 1);
    }
  }, [currentPlaylist, currentSegmentIndex, isLoadingSound]);

  const closePlayer = useCallback(async () => {
    await unloadSound();
    setCurrentPlaylist(null);
    setCurrentSegmentIndex(0);
    setPlaybackState(initialPlaybackState);
  }, [unloadSound]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      unloadSound();
    };
  }, [unloadSound]);

  const value: AudioPlayerContextType = {
    playbackState,
    currentPlaylist,
    currentSegmentIndex,
    isLoadingSound,
    loadPlaylist,
    togglePlay,
    seekTo,
    seekBy,
    nextSegment,
    previousSegment,
    closePlayer,
  };

  return (
    <AudioPlayerContext.Provider value={value}>
      {children}
    </AudioPlayerContext.Provider>
  );
}
