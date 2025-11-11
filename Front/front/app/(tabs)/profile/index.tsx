import { useRouter } from 'expo-router';
import { Alert, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { useAuth } from '@/providers/AuthProvider';

type MenuItem = {
  label: string;
  onPress: () => void;
};

export default function ProfileScreen() {
  const router = useRouter();
  const { signOut, deleteAccount } = useAuth();

  const handleSignOut = () => {
    Alert.alert('로그아웃', '정말 로그아웃하시겠어요?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: async () => {
          await signOut();
          // 상태 업데이트로 탭 레이아웃에서 자동 리디렉션되지만, 즉시 이동을 보장하기 위해 처리
          router.replace('/(auth)/login' as any);
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
            router.replace('/(auth)/login' as any);
            return;
          }
          Alert.alert('안내', '계정 삭제에 실패했습니다. 잠시 후 다시 시도해주세요.');
        },
      },
    ]);
  };

  const menuItems: MenuItem[] = [
    { label: '알림 설정', onPress: () => router.push('/(tabs)/profile/notifications') },
    { label: '난이도 설정', onPress: () => router.push('/(tabs)/profile/difficulty') },
    { label: '로그아웃', onPress: handleSignOut },
    { label: '회원탈퇴', onPress: handleDeleteAccount },
  ];

  return (
    <SafeAreaView style={styles.container}>
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
