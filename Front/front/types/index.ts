export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

export type Topic = {
  id: string;
  name: string;
  summary: string;
  image_uri: string;
};

export type FeedItem = {
  id: string;
  title: string;
  date: string;
  summary: string;
  content: string;
  imageUri: string;
  topic: string;  // Topic 이름
  topicId?: string;  // Topic ID (옵션)
};
