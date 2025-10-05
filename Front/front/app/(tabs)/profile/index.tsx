import { useRouter } from 'expo-router';
import { SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

type MenuItem = {
  label: string;
  onPress: () => void;
};

export default function ProfileScreen() {
  const router = useRouter();

  const menuItems: MenuItem[] = [
    { label: '알림 설정', onPress: () => router.push('/(tabs)/profile/notifications') },
    { label: '로그아웃', onPress: () => {} },
    { label: '회원탈퇴', onPress: () => {} },
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
