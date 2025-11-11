import { useRouter } from 'expo-router';
import { Alert, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { useAuth } from '@/providers/AuthProvider';

type MenuItem = {
  label: string;
  onPress: () => void;
};

export default function ProfileScreen() {
  const router = useRouter();
  const { user, signOut, deleteAccount } = useAuth();

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일 가입`;
    } catch {
      return dateString;
    }
  };

  const handleSignOut = () => {
    Alert.alert('로그아웃', '정말 로그아웃하시겠어요?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: async () => {
          await signOut();
          // TabsLayout의 Redirect에서 자동으로 /(auth)/login으로 리다이렉션됨
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert('회원탈퇴', '계정을 삭제하면 되돌릴 수 없습니다. 진행하시겠어요?', [
      { text: '취소', style: 'cancel' },
      {
        text: '탈퇴',
        style: 'destructive',
        onPress: async () => {
          const success = await deleteAccount();
          if (success) {
            Alert.alert('안내', '계정이 삭제되었습니다.');
            // TabsLayout의 Redirect에서 자동으로 /(auth)/login으로 리다이렉션됨
            return;
          }
          Alert.alert('안내', '계정 삭제에 실패했습니다. 잠시 후 다시 시도해주세요.');
        },
      },
    ]);
  };

  const menuItems: MenuItem[] = [
    { label: '구독 관리', onPress: () => router.push('/(tabs)/profile/subscriptions') },
    { label: '알림 설정', onPress: () => router.push('/(tabs)/profile/notifications') },
    { label: '난이도 설정', onPress: () => router.push('/(tabs)/profile/difficulty') },
    { label: '로그아웃', onPress: handleSignOut },
    { label: '회원탈퇴', onPress: handleDeleteAccount },
  ];

  return (
    <SafeAreaView style={styles.container}>
      {/* 사용자 정보 헤더 */}
      <View style={styles.userInfoSection}>
        <Text style={styles.greeting}>
          {user?.nickname || '사용자'}님 안녕하세요!
        </Text>
        <Text style={styles.email}>{user?.email || ''}</Text>
        <Text style={styles.joinDate}>{user?.createdAt ? formatDate(user.createdAt) : ''}</Text>
      </View>

      {/* 메뉴 리스트 */}
      <View style={styles.listWrapper}>
        {menuItems.map((item) => (
          <TouchableOpacity
            key={item.label}
            style={styles.listItem}
            activeOpacity={0.7}
            onPress={item.onPress}
          >
            <Text style={styles.listItemText}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  userInfoSection: {
    paddingHorizontal: 24,
    paddingVertical: 32,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    backgroundColor: '#fafafa',
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  email: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  joinDate: {
    fontSize: 13,
    color: '#9ca3af',
  },
  listWrapper: {
    paddingVertical: 16,
  },
  listItem: {
    paddingVertical: 20,
    paddingHorizontal: 24,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#e5e7eb',
  },
  listItemText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
  },
});
