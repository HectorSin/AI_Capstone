import { useEffect, useMemo, useState } from 'react';
import { Alert, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { NavigationHeader } from '@/components/NavigationHeader';
import { API_BASE_URL } from '@/utils/api';
import { useAuth } from '@/providers/AuthProvider';
import type { Topic } from '@/types';

export default function SubscriptionsScreen() {
  const router = useRouter();
  const { token, refreshSubscribedTopics } = useAuth();

  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [initialSelectedIds, setInitialSelectedIds] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  // 전체 토픽 로드
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`${API_BASE_URL}/topics/`, { headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error('Failed to fetch topics');
        const data = await response.json();
        setTopics(
          data.map((t: any) => ({
            id: t.id,
            name: t.name,
            summary: t.summary ?? t.name,
          }))
        );
      } catch (error) {
        console.warn('[Subscriptions] fetch topics failed', error);
        Alert.alert('안내', '토픽 목록을 불러오지 못했습니다.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchTopics();
  }, []);

  // 사용자의 구독 토픽 로드
  useEffect(() => {
    const fetchPreferred = async () => {
      if (!token) return;
      try {
        const response = await fetch(`${API_BASE_URL}/users/me/topics`, {
          headers: {
            Accept: 'application/json',
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) throw new Error('Failed to fetch my topics');
        const data = await response.json();
        const ids: string[] = data.map((t: any) => t.id);
        setSelectedIds(ids);
        setInitialSelectedIds(ids);
      } catch (error) {
        console.warn('[Subscriptions] fetch my topics failed', error);
      }
    };
    fetchPreferred();
  }, [token]);

  const toggle = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const isDirty = useMemo(() => {
    const a = new Set(initialSelectedIds);
    const b = new Set(selectedIds);
    if (a.size !== b.size) return true;
    for (const id of a) if (!b.has(id)) return true;
    return false;
  }, [initialSelectedIds, selectedIds]);

  const handleSave = async () => {
    if (!token) {
      Alert.alert('안내', '로그인이 필요합니다.');
      return;
    }
    try {
      setIsSaving(true);
      // 차이 계산
      const prev = new Set(initialSelectedIds);
      const next = new Set(selectedIds);
      const toAdd = [...next].filter((id) => !prev.has(id));
      const toRemove = [...prev].filter((id) => !next.has(id));

      // 추가
      for (const topicId of toAdd) {
        await fetch(`${API_BASE_URL}/users/me/topics/${topicId}`, {
          method: 'POST',
          headers: {
            Accept: 'application/json',
            Authorization: `Bearer ${token}`,
          },
        });
      }
      // 제거
      for (const topicId of toRemove) {
        await fetch(`${API_BASE_URL}/users/me/topics/${topicId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
      setInitialSelectedIds(selectedIds);
      await refreshSubscribedTopics();
      Alert.alert('안내', '구독 토픽이 저장되었습니다.');
      router.back();
    } catch (error) {
      console.warn('[Subscriptions] save failed', error);
      Alert.alert('안내', '저장 중 문제가 발생했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <NavigationHeader
        title="구독 관리"
        onBack={() => router.back()}
        rightButton={{ text: isSaving ? '저장 중' : '저장', onPress: handleSave, disabled: isSaving || isLoading || !isDirty }}
      />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>관심 토픽 선택</Text>
        <Text style={styles.subtitle}>구독할 토픽을 선택/해제하세요.</Text>
        <View style={styles.form}>
          {isLoading ? (
            <Text style={styles.helperText}>불러오는 중...</Text>
          ) : topics.length === 0 ? (
            <Text style={styles.errorText}>토픽이 없습니다.</Text>
          ) : (
            topics.map((topic) => {
              const active = selectedIds.includes(topic.id);
              return (
                <Pressable
                  key={topic.id}
                  onPress={() => toggle(topic.id)}
                  style={({ pressed }) => [styles.topicCard, active && styles.topicCardSelected, pressed && styles.topicCardPressed]}
                >
                  <Text style={[styles.topicTitle, active && styles.topicTitleSelected]}>{topic.name}</Text>
                  <Text style={styles.topicDescription}>{topic.summary}</Text>
                </Pressable>
              );
            })
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  container: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
    gap: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
  },
  subtitle: {
    fontSize: 14,
    color: '#6b7280',
  },
  form: {
    gap: 12,
  },
  helperText: {
    fontSize: 13,
    color: '#6b7280',
  },
  errorText: {
    fontSize: 13,
    color: '#dc2626',
  },
  topicCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    backgroundColor: '#fff',
  },
  topicCardSelected: {
    borderColor: '#2563eb',
    backgroundColor: '#dbeafe',
  },
  topicCardPressed: {
    opacity: 0.8,
  },
  topicTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
    color: '#374151',
  },
  topicTitleSelected: {
    color: '#1d4ed8',
  },
  topicDescription: {
    fontSize: 13,
    color: '#6b7280',
  },
});
