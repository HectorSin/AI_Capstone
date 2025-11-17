export type PodcastSegment = {
  article_id: string;
  topic_id: string;
  topic_name: string;
  title: string;
  audio_url: string;
  duration_seconds: number;
  source_url?: string;
};

export type DailyPodcastSummary = {
  date: string;
  article_count: number;
  total_duration_seconds: number;
  topics: string[];
  segments: PodcastSegment[];
};
