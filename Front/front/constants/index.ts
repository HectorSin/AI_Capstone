import type { DifficultyLevel } from '@/types';

export const DIFFICULTY_OPTIONS: {
  value: DifficultyLevel;
  label: string;
  description: string;
}[] = [
  {
    value: 'beginner',
    label: 'Beginner',
    description: '기초부터 차근차근 배우고 싶어요',
  },
  {
    value: 'intermediate',
    label: 'Intermediate',
    description: '기본 지식이 있고, 심화 내용을 원해요',
  },
  {
    value: 'advanced',
    label: 'Advanced',
    description: '전문적이고 깊이 있는 내용을 원해요',
  },
];
