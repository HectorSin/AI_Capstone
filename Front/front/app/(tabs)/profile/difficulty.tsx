import { useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
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
  const [initialDifficulty, setInitialDifficulty] = useState<DifficultyLevel>('intermediate');
  const [isUpdating, setIsUpdating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadCurrentDifficulty = async () => {
      setIsLoading(true);
      try {
        await refreshProfile();
        if (user?.difficulty_level) {
          const level = user.difficulty_level as DifficultyLevel;
          setSelectedDifficulty(level);
          setInitialDifficulty(level);
        }
      } catch (error) {
        console.warn('[Difficulty] Failed to load user profile', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadCurrentDifficulty();
  }, []);

  const isDirty = useMemo(() => {
    return selectedDifficulty !== initialDifficulty;
  }, [selectedDifficulty, initialDifficulty]);

  const handleSave = async () => {
    if (!selectedDifficulty) {
      Alert.alert('안내', '난이도를 선택해주세요.');
      return;
    }

    if (!isDirty) {
      Alert.alert('안내', '변경사항이 없습니다.');
      return;
    }

    setIsUpdating(true);
    try {
      const success = await updateDifficulty(selectedDifficulty);

      if (success) {
        Alert.alert('성공', '난이도 설정이 변경되었습니다.');
        setInitialDifficulty(selectedDifficulty);
      } else {
        Alert.alert('안내', '난이도 설정 변경에 실패했습니다. 다시 시도해주세요.');
      }
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
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.loadingText}>불러오는 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* 헤더 바 */}
      <View style={styles.headerBar}>
        <Pressable
          onPress={() => router.back()}
          hitSlop={8}
          style={({ pressed }) => [styles.headerButton, pressed && styles.buttonPressed]}
        >
          <Text style={styles.backText}>뒤로</Text>
        </Pressable>
        <Text style={styles.headerTitle}>난이도 설정</Text>
        <Pressable
          disabled={!isDirty || isUpdating}
          onPress={handleSave}
          hitSlop={8}
          style={({ pressed }) => [
            styles.headerButton,
            (!isDirty || isUpdating) && styles.headerButtonDisabled,
            pressed && isDirty && !isUpdating && styles.buttonPressed,
          ]}
        >
          <Text style={[styles.saveText, (!isDirty || isUpdating) && styles.saveTextDisabled]}>
            {isUpdating ? '저장 중' : '저장'}
          </Text>
        </Pressable>
      </View>

      {/* 컨텐츠 */}
      <View style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>학습 난이도</Text>
          <Text style={styles.sectionDescription}>선호하는 학습 난이도를 선택해주세요.</Text>
          <View style={styles.optionsContainer}>
            {DIFFICULTY_OPTIONS.map((option) => {
              const isSelected = selectedDifficulty === option.value;
              return (
                <Pressable
                  key={option.value}
                  onPress={() => setSelectedDifficulty(option.value)}
                  style={({ pressed }) => [
                    styles.optionButton,
                    isSelected && styles.optionButtonSelected,
                    pressed && styles.optionButtonPressed,
                  ]}
                >
                  <View style={styles.optionContent}>
                    <Text style={[styles.optionLabel, isSelected && styles.optionLabelSelected]}>
                      {option.label}
                    </Text>
                    <Text style={[styles.optionDescription, isSelected && styles.optionDescriptionSelected]}>
                      {option.description}
                    </Text>
                  </View>
                </Pressable>
              );
            })}
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
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
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#e5e7eb',
    backgroundColor: '#ffffff',
  },
  headerButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  headerButtonDisabled: {
    opacity: 0.4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  backText: {
    fontSize: 14,
    color: '#2563eb',
  },
  saveText: {
    fontSize: 14,
    color: '#2563eb',
    fontWeight: '600',
  },
  saveTextDisabled: {
    color: '#9ca3af',
  },
  buttonPressed: {
    opacity: 0.5,
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
  },
  section: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 20,
    gap: 12,
  },
  sectionLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  sectionDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  optionsContainer: {
    gap: 12,
  },
  optionButton: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#d1d5db',
    backgroundColor: '#ffffff',
  },
  optionButtonSelected: {
    borderColor: '#2563eb',
    backgroundColor: '#dbeafe',
  },
  optionButtonPressed: {
    opacity: 0.7,
  },
  optionContent: {
    gap: 4,
  },
  optionLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  optionLabelSelected: {
    color: '#1d4ed8',
  },
  optionDescription: {
    fontSize: 14,
    color: '#6b7280',
  },
  optionDescriptionSelected: {
    color: '#1e40af',
  },
});
