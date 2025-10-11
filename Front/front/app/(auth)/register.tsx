import { Link, useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { useAuth } from '@/providers/AuthProvider';

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!email || !password || !confirmPassword) {
      Alert.alert('안내', '모든 필드를 입력해주세요.');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('안내', '비밀번호가 일치하지 않습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      const success = await signUp({ email, password });
      if (success) {
        router.replace('/(tabs)' as any);
        return;
      }

      Alert.alert('안내', '회원가입에 실패했습니다. 다시 시도해주세요.');
    } catch (error) {
      console.warn('signUp failed', error);
      Alert.alert('안내', '회원가입 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>새 계정 만들기</Text>
      <Text style={styles.subtitle}>몇 가지 정보만 입력하면 바로 사용할 수 있어요.</Text>

      <View style={styles.form}>
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="이메일"
          keyboardType="email-address"
          autoCapitalize="none"
          style={styles.input}
        />
        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="비밀번호"
          secureTextEntry
          style={styles.input}
        />
        <TextInput
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          placeholder="비밀번호 확인"
          secureTextEntry
          style={styles.input}
        />
        <Pressable style={[styles.button, isSubmitting && styles.buttonDisabled]} onPress={handleSubmit} disabled={isSubmitting}>
          <Text style={styles.buttonText}>{isSubmitting ? '가입 중...' : '회원가입'}</Text>
        </Pressable>
      </View>

      <Text style={styles.footerText}>
        이미 계정이 있다면{' '}
        <Link href="/(auth)/login" asChild>
          <Pressable>
            <Text style={styles.link}>로그인</Text>
          </Pressable>
        </Link>
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 80,
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },
  form: {
    gap: 16,
  },
  input: {
    height: 52,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#d1d5db',
    backgroundColor: '#fff',
  },
  button: {
    height: 52,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#22c55e',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  footerText: {
    marginTop: 24,
    fontSize: 14,
    color: '#4b5563',
  },
  link: {
    color: '#2563eb',
    fontWeight: '600',
  },
});
