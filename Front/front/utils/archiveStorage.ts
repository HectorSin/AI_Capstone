import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system';

import type { DailyPodcastSummary } from '@/types/podcast';

const STORAGE_KEY = '@archive/downloads';
export type DownloadedSegment = {
  articleId: string;
  fileUri: string;
  durationSeconds: number;
  title: string;
  topicName: string;
};

export type DownloadedPlaylist = {
  id: string;
  date: string;
  topics: string[];
  totalDurationSeconds: number;
  segments: DownloadedSegment[];
  createdAt: number;
};

async function readStorage(): Promise<DownloadedPlaylist[]> {
  const raw = await AsyncStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as DownloadedPlaylist[];
  } catch (error) {
    console.warn('[ArchiveStorage] Failed to parse downloads', error);
    return [];
  }
}

async function writeStorage(items: DownloadedPlaylist[]) {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export async function listDownloadedPlaylists(): Promise<DownloadedPlaylist[]> {
  return readStorage();
}

export async function removeDownloadedPlaylist(id: string) {
  const items = await readStorage();
  const target = items.find((item) => item.id === id);
  if (target) {
    await Promise.all(
      target.segments.map(async (segment) => {
        try {
          await FileSystem.deleteAsync(segment.fileUri, { idempotent: true });
        } catch (error) {
          console.warn('[ArchiveStorage] Failed to delete segment file', error);
        }
      })
    );
  }
  const filtered = items.filter((item) => item.id !== id);
  await writeStorage(filtered);
}

async function ensureDownloadDir() {
  const root = (FileSystem as any).documentDirectory ?? (FileSystem as any).cacheDirectory;
  if (!root) {
    throw new Error('Download directory is not available');
  }
  const dir = `${root}archive/`;
  const dirInfo = await FileSystem.getInfoAsync(dir);
  if (!dirInfo.exists) {
    await FileSystem.makeDirectoryAsync(dir, { intermediates: true });
  }
  return dir;
}

export async function downloadPlaylist(summary: DailyPodcastSummary): Promise<DownloadedPlaylist> {
  const downloadDir = await ensureDownloadDir();
  const segments: DownloadedSegment[] = [];

  for (const segment of summary.segments) {
    const safeTopic = segment.topic_name.replace(/[^a-zA-Z0-9_-]/g, '_');
    const fileName = `${summary.date}_${safeTopic}_${segment.article_id}.mp3`;
    const targetPath = `${downloadDir}${fileName}`;
    const downloadResult = await FileSystem.downloadAsync(segment.audio_url, targetPath);
    segments.push({
      articleId: segment.article_id,
      fileUri: downloadResult.uri,
      durationSeconds: segment.duration_seconds,
      title: segment.title,
      topicName: segment.topic_name,
    });
  }

  const newEntry: DownloadedPlaylist = {
    id: `${summary.date}_${Date.now()}`,
    date: summary.date,
    topics: summary.topics,
    totalDurationSeconds: summary.total_duration_seconds,
    segments,
    createdAt: Date.now(),
  };

  const existing = await readStorage();
  await writeStorage([newEntry, ...existing]);
  return newEntry;
}
