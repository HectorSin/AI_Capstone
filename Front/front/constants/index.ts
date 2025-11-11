import type { DifficultyLevel } from '@/types';

export const DIFFICULTY_OPTIONS: {
  value: DifficultyLevel;
  label: string;
  description: string;
}[] = [
  {
    value: 'beginner',
    label: '초급 (하)',
    description: '기초부터 차근차근 배우고 싶어요',
  },
  {
    value: 'intermediate',
    label: '중급 (중)',
    description: '기본 지식이 있고, 심화 내용을 원해요',
  },
  {
    value: 'advanced',
    label: '고급 (상)',
    description: '전문적이고 깊이 있는 내용을 원해요',
  },
];
