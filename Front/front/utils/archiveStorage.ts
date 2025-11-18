import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system/legacy';

import type { DailyPodcastSummary } from '@/types/podcast';
import { API_BASE_URL, getAuthTokenValue } from '@/utils/api';

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
  difficulty: string; // 'beginner', 'intermediate', 'advanced'
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
  const root = FileSystem.documentDirectory ?? FileSystem.cacheDirectory;
  console.log('[ArchiveStorage] resolve directories', {
    documentDirectory: FileSystem.documentDirectory,
    cacheDirectory: FileSystem.cacheDirectory,
    resolved: root,
  });
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
  const authToken = await getAuthTokenValue();

  // 첫 번째 세그먼트의 난이도를 대표 난이도로 사용 (모든 세그먼트가 같은 난이도)
  const difficulty = summary.segments[0]?.difficulty || 'intermediate';

  for (const segment of summary.segments) {
    const safeTopic = segment.topic_name.replace(/[^a-zA-Z0-9_-]/g, '_');
    const fileName = `${summary.date}_${difficulty}_${safeTopic}_${segment.article_id}.mp3`;
    const targetPath = `${downloadDir}${fileName}`;
    const downloadSource = resolveAudioUrl(segment.audio_url);
    const options = authToken
      ? { headers: { Authorization: `Bearer ${authToken}` } }
      : undefined;
    const downloadResult = await FileSystem.downloadAsync(downloadSource, targetPath, options);
    segments.push({
      articleId: segment.article_id,
      fileUri: downloadResult.uri,
      durationSeconds: segment.duration_seconds,
      title: segment.title,
      topicName: segment.topic_name,
    });
  }

  const newEntry: DownloadedPlaylist = {
    id: `${summary.date}_${difficulty}_${Date.now()}`,
    date: summary.date,
    difficulty,
    topics: summary.topics,
    totalDurationSeconds: summary.total_duration_seconds,
    segments,
    createdAt: Date.now(),
  };

  const existing = await readStorage();
  await writeStorage([newEntry, ...existing]);
  return newEntry;
}

function resolveAudioUrl(url: string) {
  if (!url) {
    return '';
  }
  if (/^https?:\/\//i.test(url)) {
    return url;
  }
  return `${API_BASE_URL}${url}`;
}
