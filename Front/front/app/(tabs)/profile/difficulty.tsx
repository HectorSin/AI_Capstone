import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, SafeAreaView, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/providers/AuthProvider';

type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

const DIFFICULTY_OPTIONS: {
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

export default function DifficultySettingScreen() {
  const router = useRouter();
  const { user, updateDifficulty, refreshProfile } = useAuth();

  const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel>('intermediate');
  const [isUpdating, setIsUpdating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadCurrentDifficulty = async () => {
      setIsLoading(true);
      try {
        await refreshProfile();
        if (user?.difficulty_level) {
          setSelectedDifficulty(user.difficulty_level as DifficultyLevel);
        }
      } catch (error) {
        console.warn('[Difficulty] Failed to load user profile', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadCurrentDifficulty();
  }, []);

  const handleSave = async () => {
    if (!selectedDifficulty) {
      Alert.alert('안내', '난이도를 선택해주세요.');
      return;
    }

    // 변경사항이 없으면 저장하지 않음
    if (user?.difficulty_level === selectedDifficulty) {
      Alert.alert('안내', '변경사항이 없습니다.');
      return;
    }

    setIsUpdating(true);
    try {
      const success = await updateDifficulty(selectedDifficulty);

      if (success) {
        Alert.alert('성공', '난이도 설정이 변경되었습니다.', [
          {
            text: '확인',
            onPress: () => router.back(),
          },
        ]);
        return;
      }

      Alert.alert('안내', '난이도 설정 변경에 실패했습니다. 다시 시도해주세요.');
    } catch (error) {
      console.warn('[Difficulty] Update failed', error);
      Alert.alert('안내', '난이도 설정 변경 중 문제가 발생했습니다.');
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#22c55e" />
          <Text style={styles.loadingText}>불러오는 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>학습 난이도 설정</Text>
        <Text style={styles.subtitle}>선호하는 학습 난이도를 선택해주세요.</Text>

        <View style={styles.optionsContainer}>
          {DIFFICULTY_OPTIONS.map((option) => {
            const isSelected = selectedDifficulty === option.value;
            return (
              <Pressable
                key={option.value}
                style={[styles.optionCard, isSelected && styles.optionCardSelected]}
                onPress={() => setSelectedDifficulty(option.value)}
              >
                <Text style={[styles.optionTitle, isSelected && styles.optionTitleSelected]}>
                  {option.label}
                </Text>
                <Text style={styles.optionDescription}>{option.description}</Text>
              </Pressable>
            );
          })}
        </View>

        <View style={styles.buttonContainer}>
          <Pressable
            style={[styles.button, styles.buttonSecondary]}
            onPress={() => router.back()}
            disabled={isUpdating}
          >
            <Text style={styles.buttonTextSecondary}>취소</Text>
          </Pressable>

          <Pressable
            style={[styles.button, styles.buttonPrimary, isUpdating && styles.buttonDisabled]}
            onPress={handleSave}
            disabled={isUpdating}
          >
            {isUpdating ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>저장</Text>
            )}
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 32,
    paddingBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
    color: '#111827',
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },
  optionsContainer: {
    flex: 1,
    gap: 12,
  },
  optionCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    backgroundColor: '#fff',
  },
  optionCardSelected: {
    borderColor: '#22c55e',
    backgroundColor: '#f0fdf4',
  },
  optionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
    color: '#374151',
  },
  optionTitleSelected: {
    color: '#22c55e',
  },
  optionDescription: {
    fontSize: 14,
    color: '#6b7280',
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  button: {
    flex: 1,
    height: 52,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonPrimary: {
    backgroundColor: '#22c55e',
  },
  buttonSecondary: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonTextSecondary: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '600',
  },
});
