import { SafeAreaView, FlatList, StyleSheet, Text, View, Alert, ActivityIndicator } from 'react-native';
import { useCallback, useEffect, useState } from 'react';

import { ArchiveCard } from '@/components/ArchiveCard';
import { useAuth } from '@/providers/AuthProvider';
import { fetchArchive, ArchiveItem as ArchiveItemType, API_BASE_URL } from '@/utils/api';

export default function ArchiveScreen() {
  const { token } = useAuth();
  const [archiveItems, setArchiveItems] = useState<ArchiveItemType[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());

  const loadArchive = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const items = await fetchArchive(token);
      setArchiveItems(items);
    } catch (error) {
      console.error('아카이브 로드 실패:', error);
      Alert.alert('오류', '아카이브를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadArchive();
  }, [loadArchive]);

  const handleDownload = useCallback(
    async (item: ArchiveItemType) => {
      if (!token) {
        console.debug('[Download] ❌ 토큰이 없습니다.');
        return;
      }

      if (downloadingIds.has(item.id)) {
        console.debug('[Download] ⏳ 이미 다운로드 중입니다:', item.id);
        return;
      }

      try {
        setDownloadingIds((prev) => new Set(prev).add(item.id));

        const downloadUrl = `${API_BASE_URL}/podcasts/${item.id}/download`;
        
        console.debug('[Download] 🚀 다운로드 시작');
        console.debug('[Download] 📦 아이템 정보:', {
          id: item.id,
          title: item.title,
          date: item.date,
          keywords: item.keywords,
        });
        console.debug('[Download] 🔗 API URL:', downloadUrl);
        console.debug('[Download] 🔑 토큰:', token ? `${token.substring(0, 20)}...` : '없음');

        // API 연결 테스트 (HEAD 요청 또는 실제 다운로드 요청)
        const response = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        console.debug('[Download] 📡 API 응답 상태:', response.status);
        console.debug('[Download] 📡 API 응답 헤더:', {
          'content-type': response.headers.get('content-type'),
          'content-length': response.headers.get('content-length'),
        });

        if (!response.ok) {
          const errorText = await response.text().catch(() => '');
          console.debug('[Download] ❌ API 오류:', {
            status: response.status,
            statusText: response.statusText,
            error: errorText,
          });
          throw new Error(`API 오류: ${response.status} ${response.statusText}`);
        }

        console.debug('[Download] ✅ API 연결 성공!');
        console.debug('[Download] ✅ 다운로드 가능한 파일 확인됨');

        // 실제 다운로드는 하지 않고 로그만 출력
        console.debug('[Download] ℹ️ 디버그 모드: 실제 파일 다운로드는 수행하지 않습니다.');

      } catch (error) {
        console.debug('[Download] ❌ 다운로드 실패:', error);
        if (error instanceof Error) {
          console.debug('[Download] ❌ 에러 메시지:', error.message);
          console.debug('[Download] ❌ 에러 스택:', error.stack);
        }
      } finally {
        setDownloadingIds((prev) => {
          const next = new Set(prev);
          next.delete(item.id);
          return next;
        });
        console.debug('[Download] 🏁 다운로드 프로세스 완료');
      }
    },
    [token, downloadingIds]
  );

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.loadingText}>아카이브를 불러오는 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={archiveItems}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ArchiveCard
            date={formatDate(item.date)}
            keywords={item.keywords}
            durationSeconds={item.duration ?? undefined}
            onPressDownload={() => handleDownload(item)}
          />
        )}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        refreshing={loading}
        onRefresh={loadArchive}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>보관된 피드가 없어요</Text>
            <Text style={styles.emptyBody}>흥미로운 소식을 보관하면 여기에서 다시 확인할 수 있어요.</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  listContent: {
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
  },
  emptyState: {
    alignItems: 'center',
    gap: 12,
    marginTop: 72,
    paddingHorizontal: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
  },
  emptyBody: {
    fontSize: 15,
    color: '#6b7280',
    textAlign: 'center',
  },
});
